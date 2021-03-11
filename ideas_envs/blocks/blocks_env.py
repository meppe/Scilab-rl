import os
import numpy as np
from gym.utils import EzPickle
from gym.envs.robotics import fetch_env, rotations, utils

MODEL_XML_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'blocks.xml')


class BlocksEnv(fetch_env.FetchEnv, EzPickle):
    """
    Environment for block-stacking. Up to four blocks can be stacked.
    """

    def __init__(self, n_objects, gripper_goal, reward_type='sparse', model_xml_path=MODEL_XML_PATH):
        """
        :param n_objects: How many blocks should be stacked
        :param gripper_goal: 3 possibilities:
            gripper_none: The position of the gripper is not relevant for the goal
            gripper_random: The gripper should reach a random position after stacking the blocks
            gripper_above: The gripper should be above the stacked blocks
        :param reward_type: Whether the reward should be sparse or dense
        :param model_xml_path: The path to the XML that defines the MuJoCo environment
        """
        initial_qpos = {
            # robot xyz
            'robot0:slide0': -0.65,
            'robot0:slide1': 0,
            'robot0:slide2': 0,
        }

        self.n_objects = n_objects
        self.gripper_goal = gripper_goal

        self.goal_size = self.n_objects * 3
        if self.gripper_goal != 'gripper_none':
            self.goal_size += 3
        self.object_height = 0.05
        self.table_height = 0.4
        self.sample_dist_threshold = np.sqrt(2 * self.object_height**2)

        has_object = self.n_objects > 0

        super().__init__(model_xml_path, has_object=has_object, block_gripper=False, n_substeps=20,
                         gripper_extra_height=0.2, target_in_the_air=True, target_offset=0.0,
                         obj_range=0.15, target_range=0.15, distance_threshold=0.05,
                         initial_qpos=initial_qpos, reward_type=reward_type)
        EzPickle.__init__(self)

    def _get_obs(self):
        grip_pos = self.sim.data.get_site_xpos('robot0:grip')
        dt = self.sim.nsubsteps * self.sim.model.opt.timestep
        grip_velp = self.sim.data.get_site_xvelp('robot0:grip') * dt
        robot_qpos, robot_qvel = utils.robot_get_obs(self.sim)
        gripper_state = robot_qpos[-2:]
        gripper_vel = robot_qvel[-2:] * dt

        object_pos, object_rot, object_velp, object_velr = (np.empty(self.n_objects * 3) for _ in range(4))
        for i in range(self.n_objects):
            # position
            object_pos[i * 3:(i + 1) * 3] = self.sim.data.get_geom_xpos('object0')
            # rotation
            object_rot[i * 3:(i + 1) * 3] = rotations.mat2euler(self.sim.data.get_geom_xmat('object0'))
            # velocities
            object_velp[i * 3:(i + 1) * 3] = self.sim.data.get_geom_xvelp('object0') * dt
            object_velr[i * 3:(i + 1) * 3] = self.sim.data.get_geom_xvelr('object0') * dt

        obs = np.concatenate([grip_pos, object_pos, gripper_state, object_rot,
                              grip_velp, object_velp, object_velr, gripper_vel])
        if self.gripper_goal == 'gripper_none':
            achieved_goal = obs[3:3 + self.goal_size]
        else:
            achieved_goal = obs[:self.goal_size]

        return {
            'observation': obs.copy(),
            'achieved_goal': achieved_goal.copy(),
            'desired_goal': self.goal.copy(),
        }

    def _render_callback(self):
        # visualize the desired positions of the blocks and the gripper
        start_idx = 0
        if self.gripper_goal != 'gripper_none':
            start_idx = 3
            site_id = self.sim.model.site_name2id('gripper_goal')
            self.sim.model.site_pos[site_id] = self.goal[:3].copy()
        for i in range(self.n_objects):
            site_id = self.sim.model.site_name2id('object{}_goal'.format(i))
            self.sim.model.site_pos[site_id] = self.goal[start_idx + 3 * i:start_idx + 3 * i + 3].copy()

    def _reset_sim(self):
        self.sim.set_state(self.initial_state)
        # randomize start position of objects
        for o in range(self.n_objects):
            oname = 'object{}'.format(o)
            # find a position that is not too close to the gripper or another object
            too_close = True
            while too_close:
                object_xpos = self.initial_gripper_xpos[:2] \
                              + self.np_random.uniform(-self.obj_range, self.obj_range, size=2)

                closest_dist = np.linalg.norm(object_xpos - self.initial_gripper_xpos[:2])
                # Iterate through all previously placed boxes and select closest:
                for o_other in range(o):
                    other_xpos = self.sim.data.get_geom_xpos('object{}'.format(o_other))[:2]
                    dist = np.linalg.norm(object_xpos - other_xpos)
                    closest_dist = min(dist, closest_dist)
                if closest_dist > self.sample_dist_threshold:
                    too_close = False

            object_qpos = self.sim.data.get_joint_qpos('{}:joint'.format(oname))
            assert object_qpos.shape == (7,)
            object_qpos[:2] = object_xpos
            object_qpos[2] = self.table_height + (self.object_height / 2)
            self.sim.data.set_joint_qpos('{}:joint'.format(oname), object_qpos)
        self.sim.forward()
        return True

    def _sample_goal(self):
        goal = np.empty(self.goal_size)
        if self.n_objects > 0:
            # Find a random position for the tower
            lowest_block_xy = self.initial_gripper_xpos[:2]\
                               + self.np_random.uniform(-self.target_range, self.target_range, size=2)
            # the height z is set below table height for now because we add the object height later
            z = np.array([self.table_height - self.object_height * 0.5])
            # if the gripper position is included in the goal, leave the first 3 values free
            if self.gripper_goal == 'gripper_none':
                start_idx = 0
            else:
                start_idx = 3
            # set goal positions for the blocks
            for i in range(self.n_objects):
                z += self.object_height
                pos = np.concatenate([lowest_block_xy, z])
                goal[start_idx + i * 3:start_idx + i * 3 + 3] = pos

            # set the gripper_goal, if there is any
            if not self.gripper_goal == 'gripper_none':
                if self.gripper_goal == 'gripper_above':
                    z += 2 * self.object_height
                    goal[:3] = np.concatenate([lowest_block_xy, z])
                if self.gripper_goal == 'gripper_random':
                    too_close = True
                    while too_close:
                        grip_goal = self.initial_gripper_xpos \
                                    + self.np_random.uniform(-self.target_range, self.target_range, size=3)
                        closest_dist = np.inf
                        for i in range(self.n_objects):
                            closest_dist = min(closest_dist, np.linalg.norm(grip_goal - goal[3 + 3 * i:6 + 3 * i]))
                        if closest_dist > self.sample_dist_threshold:
                            too_close = False
                    goal[:3] = grip_goal
        else:
            # n_objects == 0 is only possible with 'gripper_random'
            goal[:] = self.initial_gripper_xpos \
                      + self.np_random.uniform(-self.target_range, self.target_range, size=3)

        return goal.copy()
