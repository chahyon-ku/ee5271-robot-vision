# some code from decentralized multiarm multiarm.cs.columbia.edu
# objects from eleramp/pybullet-object-models
import pybullet as pb
from . import pybullet_utils as pbu
from .ur5_robotiq_controller import UR5RobotiqPybulletController
from matplotlib import pyplot as plt
import numpy as np
import os
import argparse


def add_arguments(parser):
    parser.add_argument('--generate_data', type=bool, default=False)
    parser.add_argument('--num_data', type=int, default=10)
    parser.add_argument('--can_x', type=float, default=0.6)
    parser.add_argument('--can_y', type=float, default=0.7)


class Environment:
    def __init__(self):
        # physicsClient = pb.connect(pb.GUI, options="--width=1920 --height=1080 --mp4=pour.mp4 --mp4fps=30")
        physicsClient = pb.connect(pb.GUI, options="--width=1920 --height=1080")
        pb.configureDebugVisualizer(pb.COV_ENABLE_GUI, 0, lightPosition=[0, 0, 5])
        pb.setGravity(0, 0, -9.81)
        pb.setRealTimeSimulation(True)
        pos = [0, 0, 0]
        orn = pb.getQuaternionFromEuler([np.pi / 2.0, 0, np.pi / 2.0])
        pb.loadURDF("./simulation/room.urdf", pos, orn, useFixedBase=True)
        pos = [4, 0, 0]
        orn = pb.getQuaternionFromEuler([np.pi / 2.0, 0, 0])
        pb.loadURDF("./simulation/wall.urdf", pos, orn, useFixedBase=True)
        pos = [0, 0, 0]
        orn = pb.getQuaternionFromEuler([np.pi / 2.0, 0, -np.pi / 2.0])
        pb.loadURDF("./simulation/wall.urdf", pos, orn, useFixedBase=True)

        pb.resetDebugVisualizerCamera(cameraDistance=0.5, cameraYaw=90.0, cameraPitch=-60.0,
                                      cameraTargetPosition=[0.8, 1.0, 0.6])

        # load robots
        orn = pb.getQuaternionFromEuler([np.pi / 2.0, -np.pi / 2.0, np.pi / 2.0])
        robot_base_pose = [[0.025, 0.0, 1.42], orn]
        self.robotR = UR5RobotiqPybulletController(base_pose=robot_base_pose,
                                                   initial_arm_joint_values=[-np.pi / 2.0, np.pi, -np.pi / 2.0, 0, 0,
                                                                             0])
        robot_base_pose = [[0.025, 0.94, 1.42], orn]
        self.robotL = UR5RobotiqPybulletController(base_pose=robot_base_pose,
                                                   initial_arm_joint_values=[0, -np.pi / 2.0, -np.pi / 2.0,
                                                                             -np.pi / 2.0, -np.pi / 2.0, -np.pi / 2.0])

        # Set friction coefficients for gripper fingers
        for i in range(pb.getNumJoints(self.robotL.id)):
            pb.changeDynamics(self.robotL.id,
                              i,
                              lateralFriction=1.0,
                              spinningFriction=1.0,
                              rollingFriction=0.0001,
                              frictionAnchor=True)

        pos = [0.079, 1.166 - 0.09, 0.560]
        orn = pb.getQuaternionFromEuler([np.pi / 2.0, 0, np.pi / 2.0])
        pb.loadURDF("simulation/dual_arm_station.urdf", pos, orn, useFixedBase=True)
        pos = [0.5, 0.47, 0.560]
        orn = pb.getQuaternionFromEuler([np.pi / 2.0, 0, np.pi / 2.0])
        pb.loadURDF("simulation/table.urdf", pos, orn, useFixedBase=True)

    def generate_data(num_data=10):
        # load can
        pos = [0.5, 0.7, 0.630]
        orn = pb.getQuaternionFromEuler([np.pi / 2.0, 0, 0])
        canID = pb.loadURDF("simulation/can.urdf", pos, orn)
        pbu.step_real(1)

        # camera setup
        w = 640.0
        h = 480.0
        projectionMatrix = pb.computeProjectionMatrixFOV(
            fov=55.0,
            aspect=w / h,
            nearVal=0.25,
            farVal=1.9)

        # make sure folders exist
        os.makedirs('./data', exist_ok=True)
        os.makedirs('./data/rgb', exist_ok=True)
        os.makedirs('./data/seg', exist_ok=True)
        os.makedirs('./data/depth', exist_ok=True)

        folder = './data'
        f = open(folder + '/labels.csv', 'w')
        for i in range(num_data):
            # change light position
            lX = np.random.uniform(-1.0, 1.0)
            lY = np.random.uniform(-1.0, 1.0)
            lZ = np.random.uniform(3.0, 5.0)
            pb.configureDebugVisualizer(pb.COV_ENABLE_GUI, 1, lightPosition=[lX, lY, lZ])
            # move the camera
            eyeX = np.random.uniform(0.4, 0.6)
            eyeY = np.random.uniform(-0.3, -0.1)
            eyeZ = np.random.uniform(0.8, 1.0)
            tX = np.random.uniform(0.4, 0.6)
            tY = np.random.uniform(0.5, 0.7)
            tZ = np.random.uniform(0.4, 0.6)
            viewMatrix = pb.computeViewMatrix(
                cameraEyePosition=[eyeX, eyeY, eyeZ],
                cameraTargetPosition=[tX, tY, tZ],
                cameraUpVector=[0, 0, 1])
            # move the can
            x = np.random.uniform(0.2, 0.8)
            y = np.random.uniform(0.7, 1.0)
            pos = [x, y, 0.58]
            orn = pb.getQuaternionFromEuler([np.pi / 2.0, 0, 0])
            pb.resetBasePositionAndOrientation(canID, pos, orn)
            pbu.step_real(1)
            # capture pose and images
            pose = pb.getBasePositionAndOrientation(canID)
            width, height, rgbImg, depthImg, segImg = pb.getCameraImage(
                width=640,
                height=480,
                viewMatrix=viewMatrix,
                projectionMatrix=projectionMatrix,
                renderer=pb.ER_BULLET_HARDWARE_OPENGL)

            # write pose to csv
            s = str(i) + ', ' + str(pose[0][0]) + ', ' + str(pose[0][1]) + ', ' + \
                str(pose[0][2]) + ', ' + str(np.pi / 2.0) + ', ' + str(0.0) + ', ' + str(0.0) + '\n'
            f.write(s)
            # save images
            rgbFile = folder + '/rgb/' + str(i) + '.jpg'
            depthFile = folder + '/depth/' + str(i) + '.npy'
            segFile = folder + '/seg/' + str(i) + '.jpg'
            plt.imsave(rgbFile, rgbImg)
            np.save(depthFile, depthImg)
            plt.imsave(segFile, segImg)

        f.close()

    def grasp_can(self, x, y):
        # load cup
        pos = [0.8, 1.2, 0.70]
        orn = pb.getQuaternionFromEuler([0, 0, 0])
        pb.loadURDF("simulation/cup.urdf", pos, orn)
        # load can in position
        pos = [x, y, 0.70]
        orn = pb.getQuaternionFromEuler([np.pi / 2.0, 0, 0])
        # orn = pb.getQuaternionFromEuler([0, 0, 0])
        can_id = pb.loadURDF("simulation/can.urdf", pos, orn)
        # can_id = pb.loadURDF("environment/master_chef_can/master_chef_can.urdf", pos, orn)
        # pb.changeDynamics(can_id,
        #                   -1,
        #                   lateralFriction=1,
        #                   spinningFriction=0.5,
        #                   rollingFriction=1.0)
        pbu.step_real(1)

        # move robotL above can
        # self.ee_index = 8
        # jv = pbu.inverse_kinematics(self.robotL.id, self.ee_index, position = [x-0.14, y, 0.8], orientation = target_orn)
        self.ee_index = pbu.joint_from_name(self.robotL.id, 'tool_tip_joint')
        target_orn = pb.getQuaternionFromEuler([np.pi / 2, 0, 0])
        jv = pbu.inverse_kinematics(self.robotL.id, self.ee_index, position=[x, y, 0.8], orientation=target_orn)
        self.robotL.control_arm_joints(jv[0:6])
        pbu.step_real(1)
        # move to can
        self.robotL.cartesian_control('z', True, -0.16)
        pbu.step_real(1)
        # close gripper, lift up
        self.robotL.attach_object(can_id)
        self.robotL.close_gripper(realtime=True)
        # attach object
        self.robotL.cartesian_control('z', True, 0.2)
        pbu.step_real(1)
        target_orn = pb.getQuaternionFromEuler([np.pi / 2.0, 0, 0])
        jv = pbu.inverse_kinematics(self.robotL.id, self.ee_index, position=[0.8, 1.2, 0.8], orientation=target_orn)
        self.robotL.control_arm_joints(jv[0:6])
        pbu.step_real(1)
        target_orn = pb.getQuaternionFromEuler([-np.pi / 2.0, 0, 0])
        jv = pbu.inverse_kinematics(self.robotL.id, self.ee_index, position=[0.8, 1.2, 0.8], orientation=target_orn)
        self.robotL.control_arm_joints(jv[0:6])
        pbu.step_real(1)
        self.pour(20)
        # put can down
        target_orn = pb.getQuaternionFromEuler([np.pi / 2.0, 0, 0])
        jv = pbu.inverse_kinematics(self.robotL.id, self.ee_index, position=[0.8, 1.0, 0.8], orientation=target_orn)
        self.robotL.control_arm_joints(jv[0:6])
        pbu.step_real(1)
        target_orn = pb.getQuaternionFromEuler([np.pi / 2.0, 0, 0])
        jv = pbu.inverse_kinematics(self.robotL.id, self.ee_index, position=[0.8, 1.0, 0.64], orientation=target_orn)
        self.robotL.control_arm_joints(jv[0:6])
        pbu.step_real(1)
        self.robotL.detach()
        self.robotL.open_gripper(realtime=True)
        self.robotL.cartesian_control('x', value=-0.1)

    def pour(self, n):
        r = 0.008
        for _ in range(n):
            visualShapeId = pb.createVisualShape(shapeType=pb.GEOM_SPHERE,
                                                 rgbaColor=[0.5, 0.25, 0, 0.8],
                                                 radius=r)
            collisionShapeId = pb.createCollisionShape(shapeType=pb.GEOM_SPHERE, radius=r)
            pb.createMultiBody(baseMass=0.01,
                               baseInertialFramePosition=[0, 0, 0],
                               baseCollisionShapeIndex=collisionShapeId,
                               baseVisualShapeIndex=visualShapeId,
                               basePosition=[np.random.uniform(0.79, 0.81), 1.2, 0.68],
                               useMaximalCoordinates=True)
            pbu.step_real(0.05)


def main():
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    args = parser.parse_args()

    env = Environment()
    if args.generate_data:
        env.generate_data(args.num_data)
    else:
        env.grasp_can(args.can_x, args.can_y)
    pbu.step_real(1)
    pb.disconnect()


if __name__ == '__main__':
    main()