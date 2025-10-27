from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Fighter(Base):
    __tablename__ = "fighters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    wins = Column(Integer)
    wins_by_ko = Column(Integer)
    wins_by_submission = Column(Integer)
    wins_by_decision = Column(Integer)
    losses = Column(Integer)
    height_cms = Column(Float)
    reach_cms = Column(Float)
    avg_sig_str_landed = Column(Float)
    avg_td_landed = Column(Float)
    avg_sig_str_pct = Column(Float)
    avg_sub_att = Column(Float)
    stance = Column(String(255))
    weight_lbs = Column(Float)
    age = Column(Integer)
    ko_pct = Column(Float)
    sub_pct = Column(Float)
    dec_pct = Column(Float)
    avg_rounds = Column(Float)
    elo = Column(Float)
    opponent_elo = Column(Float)
    sig_str_absorbed = Column(Float)
    current_win_streak = Column(Integer)
    finish_l5 = Column(Integer)
    losses_by_ko = Column(Integer)
    losses_by_sub = Column(Integer)
    losses_by_dec = Column(Integer)
    win_pct = Column(Float)
    total_rounds_fought = Column(Integer)
    weight_class = Column(String(255))
    gender = Column(String(255))

    fights_as_a = relationship("Fight", foreign_keys="[Fight.fighter_a_id]")
    fights_as_b = relationship("Fight", foreign_keys="[Fight.fighter_b_id]")

