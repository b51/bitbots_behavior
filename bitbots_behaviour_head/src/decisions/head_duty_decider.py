# -*- coding:utf-8 -*-
"""
HeadDutyDecider
^^^^^^^^^^^^^^^

Entscheidet was der Kopf tun soll

History:

* 19.08.14: Created (Nils Rokita)

"""
import rospy
import time

from bitbots.modules.abstract.abstract_decision_module import AbstractDecisionModule
from bitbots.modules.abstract.abstract_module import debug_m
from bitbots.modules.behaviour.head.decisions.search_and_confirm import SearchAndConfirmBall, SearchAndConfirmEnemyGoal
from bitbots.modules.behaviour.head.decisions.continious_search import ContiniousSearch
from bitbots.util import get_config


class HeadDutyDecider(smach.State):

    def __init__(self, outcomes=['nothing', 'trackBall', 'trackGoal', 'trackBothBall', 'trackBothGoal', 'trackBothElse', 'searchAndConfirmBall', 'searchAndConfirmGoal', 'defaultSearch']):
        toggles = get_config()["Behaviour"]["Toggles"]["Head"]
        config = get_config()
        self.toggle_goal_vison_tracking = toggles["goalVisionTracking"]
        self.toggle_switch_ball_goal = toggles["switchBallGoalSearch"]
        self.confirm_time = config["Behaviour"]["Common"]["Search"]["confirmTime"]

        self.last_confirmd_goal = 0
        self.fail_goal_counter = 0
        self.ball_prio = 0
        self.goal_prio = 0
        self.trackjustball_aftergoal = False

    def execute(self, connector):

        # set priorities
        if connector.raw_vision_capsule().ball_seen():
            self.ball_prio = max(0, self.ball_prio - 3)
        else:
            self.ball_prio = min(120, self.ball_prio + 5)

        if connector.raw_vision_capsule().any_goal_seen():
            self.goal_prio = max(0, self.goal_prio - 2)
        else:
            self.goal_prio = min(100, self.goal_prio + 3)


        rospy.loginfo("GoalPrio", self.goal_prio)
        rospy.loginfo("BallPrio", self.ball_prio)
        rospy.loginfo("BallLastCOnfirmed", time.time() - connector.blackboard_capsule().get_confirmed_ball())
        rospy.loginfo("BallLastStratedconfirm", time.time() - connector.blackboard_capsule().get_started_confirm_ball())

        if connector.blackboard_capsule().is_no_head_movement_at_all():
            return 'nothing'

        if connector.blackboard_capsule().is_ball_tracking_still_active():
            return 'trackBall'

        if connector.blackboard_capsule().is_enemy_goal_tracking_still_active():
            return 'trackGoal'

        if connector.blackboard_capsule().is_tracking_both_still_active():  # todo to be tested
            rospy.loginfo("TrackbothTime", time.time())
            if time.time() - connector.blackboard_capsule().get_confirmed_ball() > 5:
                return 'trackBothBall'

            # ball long enough seen
            elif time.time() - connector.blackboard_capsule().get_confirmed_goal() > 6:
                return 'trackBothGoal'

            elif self.trackjustball_aftergoal:
                return 'trackBothElse'

        if self.toggle_switch_ball_goal:
            rospy.loginfo("Headdoes", "Priorities")
            if self.ball_prio >= self.goal_prio:
                return 'searchAndConfirmBall'
            else:
                return 'searchAndConfirmGoal'

        # Default Head Behaviour
        return 'defaultSearch'

    def get_reevaluate(self):
        return True
