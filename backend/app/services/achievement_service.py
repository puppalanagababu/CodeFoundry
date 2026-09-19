import logging
from typing import Any, Dict, List
from sqlalchemy.orm import Session, joinedload
from app.models.challenge import Challenge, ChallengeType
from app.models.evaluation import Achievement, Evaluation, EvaluationStatus, RequirementType, UserAchievement
from app.models.submission import Submission, SubmissionStatus

logger = logging.getLogger("app.services.achievements")

SEED_ACHIEVEMENTS = [
    {
        "code": "BUG_SLAYER",
        "name": "Bug Slayer",
        "description": "Passed 3 Bug Fix challenges.",
        "icon": "🐛",
        "requirement_type": RequirementType.BUG_FIX_COUNT.value,
        "requirement_value": 3,
    },
    {
        "code": "SECURITY_HUNTER",
        "name": "Security Hunter",
        "description": "Passed 3 Security challenges.",
        "icon": "🛡️",
        "requirement_type": RequirementType.SECURITY_COUNT.value,
        "requirement_value": 3,
    },
    {
        "code": "PERFORMANCE_ENGINEER",
        "name": "Performance Engineer",
        "description": "Passed 3 Performance challenges.",
        "icon": "⚡",
        "requirement_type": RequirementType.PERFORMANCE_COUNT.value,
        "requirement_value": 3,
    },
    {
        "code": "TEST_MASTER",
        "name": "Test Master",
        "description": "Passed 3 Testing challenges.",
        "icon": "🧪",
        "requirement_type": RequirementType.TESTING_COUNT.value,
        "requirement_value": 3,
    },
    {
        "code": "PERFECT_RUN",
        "name": "Perfect Run",
        "description": "Achieved 100/100 on 5 distinct challenges.",
        "icon": "🎯",
        "requirement_type": RequirementType.PERFECT_SCORE_COUNT.value,
        "requirement_value": 5,
    },
    {
        "code": "DEVFORGE_VETERAN",
        "name": "DevForge Veteran",
        "description": "Completed 10 distinct challenges.",
        "icon": "🎖️",
        "requirement_type": RequirementType.TOTAL_COMPLETED_COUNT.value,
        "requirement_value": 10,
    },
]


def seed_achievements(db: Session) -> None:
    """
    Seeds initial achievement definitions idempotently using SQLAlchemy session.
    """
    for ach_data in SEED_ACHIEVEMENTS:
        ach = db.query(Achievement).filter(Achievement.code == ach_data["code"]).first()
        if ach:
            ach.name = ach_data["name"]
            ach.description = ach_data["description"]
            ach.icon = ach_data["icon"]
            ach.requirement_type = ach_data["requirement_type"]
            ach.requirement_value = ach_data["requirement_value"]
            ach.is_active = True
        else:
            ach = Achievement(
                code=ach_data["code"],
                name=ach_data["name"],
                description=ach_data["description"],
                icon=ach_data["icon"],
                requirement_type=ach_data["requirement_type"],
                requirement_value=ach_data["requirement_value"],
                is_active=True,
            )
            db.add(ach)
    db.commit()


class AchievementService:
    """
    Deterministic Achievement & Badge Engine for DevForge.
    Evaluates completed challenge evaluations, determines milestone eligibility,
    and automatically awards badges without duplicate awards.
    """

    def award_for_user(self, db: Session, user_id: int) -> List[UserAchievement]:
        """
        Evaluates and awards all earned achievements for a given user ID.
        Idempotent: Safe to call repeatedly.
        """
        if not user_id:
            return []

        try:
            # 1. Fetch active achievements
            active_achievements = db.query(Achievement).filter(Achievement.is_active == True).all()
            if not active_achievements:
                return []

            # 2. Fetch completed evaluations on active challenges for this user
            evaluations = (
                db.query(Evaluation)
                .join(Submission, Evaluation.submission_id == Submission.id)
                .join(Challenge, Submission.challenge_id == Challenge.id)
                .options(
                    joinedload(Evaluation.submission).joinedload(Submission.challenge)
                )
                .filter(
                    Submission.user_id == user_id,
                    Evaluation.status == EvaluationStatus.COMPLETED.value,
                    Challenge.is_active == True,
                )
                .order_by(Submission.score.desc(), Evaluation.evaluated_at.desc(), Evaluation.id.desc())
                .all()
            )

            # 3. Deduplicate by challenge: select single best attempt per active challenge
            best_evals_by_challenge: Dict[int, Evaluation] = {}
            for eval_obj in evaluations:
                ch_id = eval_obj.submission.challenge_id if eval_obj.submission else None
                if ch_id is None:
                    continue

                if ch_id not in best_evals_by_challenge:
                    best_evals_by_challenge[ch_id] = eval_obj
                else:
                    current_best = best_evals_by_challenge[ch_id]
                    current_score = current_best.submission.score if current_best.submission else 0
                    new_score = eval_obj.submission.score if eval_obj.submission else 0

                    if new_score > current_score:
                        best_evals_by_challenge[ch_id] = eval_obj
                    elif new_score == current_score:
                        current_time = current_best.evaluated_at or current_best.created_at
                        new_time = eval_obj.evaluated_at or eval_obj.created_at
                        if current_time and new_time and new_time > current_time:
                            best_evals_by_challenge[ch_id] = eval_obj
                        elif current_time == new_time and eval_obj.id > current_best.id:
                            best_evals_by_challenge[ch_id] = eval_obj

            selected_evals = list(best_evals_by_challenge.values())

            # 4. Calculate metric aggregates across best attempts
            bug_fix_passed = 0
            security_passed = 0
            performance_passed = 0
            testing_passed = 0
            perfect_score_count = 0
            total_completed = 0

            for eval_obj in selected_evals:
                sub = eval_obj.submission
                if not sub or not sub.challenge:
                    continue

                is_passed = (sub.status == SubmissionStatus.PASSED.value)
                score = sub.score or 0
                ctype = sub.challenge.challenge_type

                if is_passed:
                    total_completed += 1
                    if ctype == ChallengeType.BUG_FIX.value:
                        bug_fix_passed += 1
                    elif ctype == ChallengeType.SECURITY.value:
                        security_passed += 1
                    elif ctype == ChallengeType.PERFORMANCE.value:
                        performance_passed += 1
                    elif ctype == ChallengeType.TESTING.value:
                        testing_passed += 1

                if score == 100:
                    perfect_score_count += 1

            # 5. Evaluate eligibility against active achievement requirements
            awarded: List[UserAchievement] = []

            # Pre-fetch existing user achievements to avoid duplicates
            existing_user_achs = {
                ua.achievement_id: ua
                for ua in db.query(UserAchievement).filter(UserAchievement.user_id == user_id).all()
            }

            for ach in active_achievements:
                earned = False
                req_val = ach.requirement_value

                if ach.requirement_type == RequirementType.BUG_FIX_COUNT.value:
                    earned = (bug_fix_passed >= req_val)
                elif ach.requirement_type == RequirementType.SECURITY_COUNT.value:
                    earned = (security_passed >= req_val)
                elif ach.requirement_type == RequirementType.PERFORMANCE_COUNT.value:
                    earned = (performance_passed >= req_val)
                elif ach.requirement_type == RequirementType.TESTING_COUNT.value:
                    earned = (testing_passed >= req_val)
                elif ach.requirement_type == RequirementType.PERFECT_SCORE_COUNT.value:
                    earned = (perfect_score_count >= req_val)
                elif ach.requirement_type == RequirementType.TOTAL_COMPLETED_COUNT.value:
                    earned = (total_completed >= req_val)

                if earned:
                    if ach.id not in existing_user_achs:
                        ua = UserAchievement(
                            user_id=user_id,
                            achievement_id=ach.id,
                        )
                        db.add(ua)
                        awarded.append(ua)
                    else:
                        awarded.append(existing_user_achs[ach.id])

            db.commit()
            return awarded
        except Exception as e:
            logger.exception("Error in AchievementService.award_for_user: %s", e)
            db.rollback()
            return []

    def get_user_achievements(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """
        Returns serialized list of earned achievements for a given user.
        Sorted deterministically: earned_at DESC, then name ASC.
        """
        if not user_id:
            return []

        user_achievements = (
            db.query(UserAchievement)
            .join(Achievement, UserAchievement.achievement_id == Achievement.id)
            .options(joinedload(UserAchievement.achievement))
            .filter(
                UserAchievement.user_id == user_id,
                Achievement.is_active == True,
            )
            .order_by(UserAchievement.earned_at.desc(), Achievement.name.asc())
            .all()
        )

        results = []
        for ua in user_achievements:
            ach = ua.achievement
            earned_at_str = ua.earned_at.isoformat() if ua.earned_at else None
            results.append({
                "code": ach.code,
                "name": ach.name,
                "description": ach.description,
                "icon": ach.icon,
                "earned_at": earned_at_str,
            })

        return results
