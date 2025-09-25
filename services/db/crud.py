from sqlalchemy.orm import Session
from . import models

def get_fighter_by_name(db: Session, name: str):
    """Retrieve a fighter by their name."""
    return db.query(models.Fighter).filter(models.Fighter.name == name).first()


def get_fighter_id(db: Session, fighter_name: str):
    """Retrieve a fighter's ID by their name."""
    fighter = db.query(models.Fighter).filter(models.Fighter.name == fighter_name).first()
    return fighter.id if fighter else None

def remove_fighter(db: Session, fighter_name: str):
    """Remove a fighter by their name."""
    fighter = db.query(models.Fighter).filter(models.Fighter.name == fighter_name).first()
    if fighter is None:
        return None
    db.delete(fighter)
    db.commit()
    return fighter

def add_fighter(
        db: Session,
        name: str,
        wins: int,
        wins_by_ko: int,
        wins_by_submission: int,
        wins_by_decision: int,
        losses: int,
        height_cms: float,
        reach_cms: float,
        avg_sig_str_landed: float,
        avg_td_landed: float,
        avg_sig_str_pct: float,
        avg_sub_att: float,
        stance: str,
        weight_lbs: float,
        age: int,
        ko_pct: float,
        sub_pct: float,
        dec_pct: float,
        avg_rounds: float,
        elo: float,
        opponent_elo: float,
        sig_str_absorbed: float,
        current_win_streak: int,
        finish_l5: int,
        losses_by_ko: int,
        losses_by_sub: int,
        losses_by_dec: int,
        win_pct: float,
        total_rounds_fought: int,
        weight_class: str,
        gender: str):
    """Add a new fighter to the database."""
    fighter = models.Fighter(
        name=name,
        wins=wins,
        wins_by_ko=wins_by_ko,
        wins_by_submission=wins_by_submission,
        wins_by_decision=wins_by_decision,
        losses=losses,
        height_cms=height_cms,
        reach_cms=reach_cms,
        avg_sig_str_landed=avg_sig_str_landed,
        avg_td_landed=avg_td_landed,
        avg_sig_str_pct=avg_sig_str_pct,
        avg_sub_att=avg_sub_att,
        stance=stance,
        weight_lbs=weight_lbs,
        age=age,
        ko_pct=ko_pct,
        sub_pct=sub_pct,
        dec_pct=dec_pct,
        avg_rounds=avg_rounds,
        elo=elo,
        opponent_elo=opponent_elo,
        sig_str_absorbed=sig_str_absorbed,
        current_win_streak=current_win_streak,
        finish_l5=finish_l5,
        losses_by_ko=losses_by_ko,
        losses_by_sub=losses_by_sub,
        losses_by_dec=losses_by_dec,
        win_pct=win_pct,
        total_rounds_fought=total_rounds_fought,
        weight_class=weight_class,
        gender=gender
    )
    db.add(fighter)
    db.commit()
    db.refresh(fighter)
    return fighter

