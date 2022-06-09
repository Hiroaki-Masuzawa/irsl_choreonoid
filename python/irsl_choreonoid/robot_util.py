from cnoid.Base import *
from cnoid.BodyPlugin import *
#from cnoid.PythonSimScriptPlugin import *
import cnoid.Body
#import cnoid.Util

import cnoid.IRSLUtil as iu
import cnoid.DrawInterface as di

import cnoid.IKSolvers as IK

import numpy as np

def getItemTreeView():
    if callable(ItemTreeView.instance):
        return ItemTreeView.instance()
    else:
        return ItemTreeView.instance

def getRootItem():
    if callable(RootItem.instance):
        return RootItem.instance()
    else:
        return RootItem.instance

def getWorld():
    rI = getRootItem()
    ret = rI.findItem("World")
    if ret == None:
        ret = WorldItem()
        rI.addChildItem(ret)
        getItemTreeView().checkItem(ret)
    return ret

def cnoidPosition(rotation = None, translation = None):
  ret = np.identity(4)
  if not (rotation is None):
    ret[:3, :3] = rotation
  if not (translation is None):
    ret[:3, 3] = translation
  return ret

def cnoidRotation(cPosition):
  return cPosition[:3, :3]

def cnoidTranslation(cPosition):
  return cPosition[:3, 3]

def loadRobot(fname, name = None):
    # print('loadRobot: %s'%(fname))
    bI = BodyItem()
    bI.load(fname)
    if name:
        bI.setName(name)
    if callable(bI.body):
        rr = bI.body()
    else:
        rr = bI.body
    rr.calcForwardKinematics()
    bI.storeInitialState()
    wd = getWorld()
    if callable(wd.childItem):
        wd.insertChildItem(bI, wd.childItem())
    else:
        wd.insertChildItem(bI, wd.childItem)
    getItemTreeView().checkItem(bI)
    return rr

def findItem(name):
    return getRootItem().findItem(name)

def findRobot(name):
    ret = findItem(name)
    ## add class check...
    if callable(ret.body):
        return ret.body()
    else:
        return ret.body

def flushRobotView(name):
    findItem(name).notifyKinematicStateChange()
    #MessageView.getInstance().flush()
    MessageView.instance.flush()

class DrawCoords(object):
    def __init__(self):
        self.RLine = di.DrawInterface(np.array([1, 0, 0]))
        self.GLine = di.DrawInterface(np.array([0, 1, 0]))
        self.BLine = di.DrawInterface(np.array([0, 0, 1]))

    def hide(self):
        self.RLine.hide()
        self.GLine.hide()
        self.BLine.hide()

    def show(self):
        self.RLine.show()
        self.GLine.show()
        self.BLine.show()

    def draw(self, coords, length = 0.1, axis_size = 0.02):
        self.hide()
        MessageView.instance.flush()

        rot = iu.Position_rotation(coords)
        ax_x = length * rot[:3, 0]
        ax_y = length * rot[:3, 1]
        ax_z = length * rot[:3, 2]
        ax_vec = length * iu.normalizeVector(rot.dot(np.array([1, 1, 1])))
        pp = iu.Position_translation(coords)

        self.RLine.drawArrow(pp, pp + ax_x, axis_size, ax_vec, 15)
        self.GLine.drawArrow(pp, pp + ax_y, axis_size, ax_vec, 15)
        self.BLine.drawArrow(pp, pp + ax_z, axis_size, ax_vec, 15)

        self.show()
        MessageView.instance.flush()

class RobotModel(object):
    def __init__(self, robot):
        self.item = None
        if isinstance(robot, BodyItem):
            self.robot = robot.body
            self.item = robot
        elif isinstance(robot, cnoid.Base.Body):
            self.robot = robot
        else:
            raise TypeError('')

        self.rleg_tip_link = None
        self.rleg_tip_to_eef = None
        self.lleg_tip_link = None
        self.lleg_tip_to_eef = None

        self.rarm_tip_link = None
        self.rarm_tip_to_eef = None
        self.larm_tip_link = None
        self.larm_tip_to_eef = None

        self.head_tip_link = None
        self.head_tip_to_eef = None
        self.torso_tip_link = None
        self.torso_tip_to_eef = None

    #def robot(self):
    #    return robot

    def links(self):
        num = self.robot.numLinks
        return [ self.robot.link(n) for n in range(num) ]

    def joint_list(self):
        num = self.robot.numJoints
        return [ self.robot.joint(n) for n in range(num) ]

    def flush(self):
        if not (self.item is None):
            self.robot.calcForwardKinematics()
            self.item.notifyKinematicStateChange()
            MessageView.instance.flush()

    def angle_vector(self, angles = None):
        num = self.robot.numJoints
        if not (angles is None):
            if num != len(angles):
                raise TypeError('length of angles does not equal with robot.numJoints')
            for idx in range(num):
                self.robot.joint(idx).q = angles[idx]
            return None
        else:
            return np.array([ self.robot.joint(n).q for n in range(num) ])

    def default_pose__(self):
        pass

    def init_pose__(self):
        pass

    def set_pose(self, name):
        av = eval('self.%s_pose__()'%(name))
        self.angle_vector(av)
        return self.angle_vector()

    def end_effector(self, limb):
        return eval('self.%s_end_effector()'%(limb))

    def rleg_end_effector(self):
        return self.rleg_tip_link.getPosition().dot(self.rleg_tip_to_eef)

    def lleg_end_effector(self):
        return self.lleg_tip_link.getPosition().dot(self.lleg_tip_to_eef)

    def rarm_end_effector(self):
        return self.rarm_tip_link.getPosition().dot(self.rarm_tip_to_eef)

    def larm_end_effector(self):
        return self.larm_tip_link.getPosition().dot(self.larm_tip_to_eef)

    def head_end_effector(self):
        return self.head_tip_link.getPosition().dot(self.head_tip_to_eef)

    def torso_end_effector(self):
        return self.torso_tip_link.getPosition().dot(self.torso_tip_to_eef)

    def foot_mid_coords(self, p = 0.5):
        return iu.mid_coords(p, self.rleg_end_effector(), self.lleg_end_effector())

    def fix_leg_to_coords(self, coords, p = 0.5):
        mc = self.foot_mid_coords(p)
        rL = self.robot.rootLink
        rL.setPosition(
            (iu.PositionInverse(mc).dot(coords)).dot(rL.getPosition())
            )
        self.robot.calcForwardKinematics()

    def move_centroid_on_foot(self, p = 0.5, debug = False):
        mid_pos = self.foot_mid_coords(p)
        mid_trans = iu.Position_translation(mid_pos)

        constraints = IK.Constraints()

        rl_constraint = IK.PositionConstraint()
        rl_constraint.A_link = self.rleg_tip_link
        rl_constraint.A_localpos = self.rleg_tip_to_eef
        #constraint->B_link() = nullptr;
        rl_constraint.B_localpos = self.rleg_end_effector()
        constraints.push_back(rl_constraint)

        ll_constraint = IK.PositionConstraint()
        ll_constraint.A_link = self.lleg_tip_link
        ll_constraint.A_localpos = self.lleg_tip_to_eef
        #constraint->B_link() = nullptr;
        ll_constraint.B_localpos = self.lleg_end_effector()
        constraints.push_back(ll_constraint)

        com_constraint = IK.COMConstraint()
        com_constraint.A_robot = self.robot
        com_constraint.B_localp = mid_trans

        w = com_constraint.weight
        w[2] = 0.0
        com_constraint.weight = w
        constraints.push_back(com_constraint)

        jlim_avoid_weight_old = np.zeros(6 + self.robot.getNumJoints())
        ##dq_weight_all = np.ones(6 + self.robot.getNumJoints())
        dq_weight_all = np.array( (1,1,1,0,0,0) + self.leg_mask() )

        d_level = 0
        if debug:
            d_level = 1

        loop = IK.solveFullbodyIKLoopFast(self.robot,
                                          constraints,
                                          jlim_avoid_weight_old,
                                          dq_weight_all,
                                          20,
                                          1e-6,
                                          d_level)
        if debug:
            for cntr, const in enumerate(constraints):
                const.debuglevel = 1
                if const.checkConvergence():
                    print('constraint %d (%s) : converged'%(cntr, const))
                else:
                    print('constraint %d (%s) : NOT converged'%(cntr, const))

        return loop

    def fullbody_inverse_kinematics(self):
        pass