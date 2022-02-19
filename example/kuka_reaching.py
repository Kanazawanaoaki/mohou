import argparse
import os

from moviepy.editor import ImageSequenceClip
import numpy as np
import pybullet as pb
import pybullet_data
import tinyfk
import tqdm

from mohou.file import dump_object, get_project_dir
from mohou.types import (AngleVector, ElementSequence, MultiEpisodeChunk,
                         RGBImage, EpisodeData)


class BulletManager(object):

    def __init__(self, use_gui, urdf_path, end_effector_name):
        client = pb.connect(pb.GUI if use_gui else pb.DIRECT)
        pb.configureDebugVisualizer(pb.COV_ENABLE_GUI, 0)
        robot_id = pb.loadURDF(urdf_path)
        pbdata_path = pybullet_data.getDataPath()
        pb.loadURDF(os.path.join(pbdata_path, "samurai.urdf"))

        link_table = {pb.getBodyInfo(robot_id, physicsClientId=client)[0].decode('UTF-8'): -1}
        joint_table = {}

        def heck(path):
            return "_".join(path.split("/"))

        for _id in range(pb.getNumJoints(robot_id, physicsClientId=client)):
            joint_info = pb.getJointInfo(robot_id, _id, physicsClientId=client)
            joint_id = joint_info[0]
            joint_name = joint_info[1].decode('UTF-8')
            joint_table[joint_name] = joint_id
            name_ = joint_info[12].decode('UTF-8')
            name = heck(name_)
            link_table[name] = _id

        self._box_id = None

        self._client = client
        self._robot_id = robot_id
        self._link_table = link_table
        self._joint_table = joint_table

        self._kin_solver = tinyfk.RobotModel(urdf_path)
        self._tinyfk_joint_ids = self._kin_solver.get_joint_ids(self.joint_names)
        self._tinyfk_endeffector_id = self._kin_solver.get_link_ids([end_effector_name])[0]

    @property
    def joint_names(self):
        return list(self._joint_table.keys())

    @property
    def joint_ids(self):
        return list(self._joint_table.values())

    def joint_angles(self):
        return np.array([
            pb.getJointState(self._robot_id, joint_id, physicsClientId=self._client)[0]
            for joint_id in self.joint_ids])

    def set_joint_angles(self, joint_angles):
        assert len(joint_angles) == len(self.joint_names)
        for joint_id, joint_angle in zip(self.joint_ids, joint_angles):
            pb.resetJointState(self._robot_id, joint_id, joint_angle,
                               targetVelocity=0.0,
                               physicsClientId=self._client)

    def solve_ik(self, target_pos):
        assert len(target_pos) == 3
        return self._kin_solver.solve_inverse_kinematics(
            target_pos,
            self.joint_angles(),
            self._tinyfk_endeffector_id,
            self._tinyfk_joint_ids,
            with_base=False)

    def set_box(self, pos):
        if self._box_id is not None:
            pb.removeBody(self._box_id)
        vis_box_id = pb.createVisualShape(
            pb.GEOM_BOX,
            halfExtents=[0.05, 0.05, 0.05],
            rgbaColor=[0.0, 1.0, 0, 0.7],
            physicsClientId=self._client)
        box_id = pb.createMultiBody(basePosition=pos, baseVisualShapeIndex=vis_box_id)
        self._box_id = box_id

    def take_photo(self, resolution=1024):
        viewMatrix = pb.computeViewMatrix(
            cameraEyePosition=[1.0, -2.0, 2.5],
            cameraTargetPosition=[0.3, 0, 0],
            cameraUpVector=[0, 1, 0])

        projectionMatrix = pb.computeProjectionMatrixFOV(
            fov=45.0,
            aspect=1.0,
            nearVal=0.01,
            farVal=5.1)

        width, height, rgbImg, depthImg, segImg = pb.getCameraImage(
            width=resolution,
            height=resolution,
            viewMatrix=viewMatrix,
            projectionMatrix=projectionMatrix)
        return rgbImg, depthImg

    def kinematic_simulate(self, joint_angles_target, N=100, n_pixel=112, with_depth=False):
        N_rand = N + np.random.randint(10)
        angles_now = np.array(self.joint_angles())
        step = (np.array(joint_angles_target) - angles_now) / (N_rand - 1)
        angles_seq = ElementSequence[AngleVector]([AngleVector(angles_now + step * i) for i in range(N_rand)])

        img_seq = ElementSequence[RGBImage]([])
        for av in angles_seq:
            self.set_joint_angles(av)
            rgba, depth = self.take_photo(n_pixel)
            if with_depth:
                depth = depth.reshape(*depth.shape, 1)
                image = np.concatenate((rgba[:, :, :3], depth), axis=2)
            else:
                image = rgba[:, :, :3]
            img_seq.append(RGBImage(image))

        for i in range(30):  # augument the data (after reaching)
            img_seq.append(RGBImage(image))
            angles_seq.append(AngleVector(angles_seq[-1]))

        return img_seq, angles_seq


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--depth', action='store_true', help='with depth channel')
    parser.add_argument('--predict', action='store_true', help='prediction mode')
    parser.add_argument('-pn', type=str, default='kuka_reaching', help='project name')
    parser.add_argument('-model', type=str, default='lstm', help='propagator model name')
    parser.add_argument('-n', type=int, default=300, help='epoch num')
    parser.add_argument('-m', type=int, default=224, help='pixel num')  # same as mnist
    parser.add_argument('-seed', type=int, default=1, help='seed')  # same as mnist
    args = parser.parse_args()
    n_epoch = args.n
    n_pixel = args.m
    with_depth = args.depth
    prediction_mode = args.predict
    project_name = args.pn
    model_name = args.model
    seed = args.seed

    np.random.seed(seed)

    pbdata_path = pybullet_data.getDataPath()
    urdf_path = os.path.join(pbdata_path, 'kuka_iiwa', 'model.urdf')
    bm = BulletManager(False, urdf_path, 'lbr_iiwa_link_7')

    data_list = []
    for i in tqdm.tqdm(range(n_epoch)):
        bm.set_joint_angles([0.2 for _ in range(7)])
        while True:
            try:
                target_pos = np.array([0.5, 0.0, 0.3]) + np.random.randn(3) * np.array([0.2, 0.5, 0.1])
                angles_solved = bm.solve_ik(target_pos)
                break
            except tinyfk._inverse_kinematics.IKFail:
                pass
        bm.set_box(target_pos)
        img_seq, cmd_seq = bm.kinematic_simulate(angles_solved, n_pixel=n_pixel, with_depth=with_depth)
        data_list.append(EpisodeData((img_seq, cmd_seq)))
        chunk = MultiEpisodeChunk(data_list)
        dump_object(chunk, project_name)

    filename = os.path.join(get_project_dir(project_name), "sample.gif")
    clip = ImageSequenceClip([img for img in img_seq], fps=50)
    clip.write_gif(filename, fps=50)