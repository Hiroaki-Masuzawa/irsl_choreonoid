## cnoid.Util
import cnoid.Util as cutil
## cnoid.Body
import cnoid.Body as cbody
from cnoid.Body import Body
from cnoid.Body import Link
from cnoid.Body import Device
## assimp
from cnoid.AssimpPlugin import *
## IRSL (not base)
from cnoid.IRSLCoords import coordinates
import cnoid.IRSLCoords as IC
from irsl_choreonoid.draw_coords import GeneralDrawInterfaceWrapped as DI
from irsl_choreonoid.draw_coords import DrawCoordsListWrapped as DC
import irsl_choreonoid.make_shapes as mkshapes
import irsl_choreonoid.cnoid_util as iu
import irsl_choreonoid.robot_util as ru
from irsl_choreonoid.robot_util import RobotModelWrapped as RobotModel
## etc
import numpy as np
from numpy import array as npa
from numpy.linalg import norm
import math
from math import pi as PI
##
if iu.isInChoreonoid():
    ## in base
    import irsl_choreonoid.cnoid_base as ib
    import cnoid.Base as cbase
