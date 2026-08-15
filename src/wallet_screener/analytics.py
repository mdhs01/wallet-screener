from __future__ import annotations

from statistics import mean, pstdev
from typing import Iterable

from .models import TradeObservation, WalletMetrics


def coefficient_of_variation(values: Iterable[float]) -> float:
    values = [float(v) for v in values]
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    if avg == 0:
        return 0.0
    return abs(pstdev(values) / avg)


def normalized_stability(values: Iterable[float]) -> float:
    values = [float(v) for v in values]
    if not values:
        return 0.0
    positive = sum(1 for v in values if v > 0) / len(values)
    cv = coefficient_of_variation(values)
    return max(0.0, min(1.0, positive * (1.0 / (1.0 + cv))))


def classify_style(m: WalletMetrics) -> str:
    hold = m.avg_hold_minutes
    freq = m.tx_7d
    if hold < 60 and freq >= 100:
        return "scalper"
    if hold <= 24 * 60:
        return "early_runner" if m.early_entry_rate >= 0.50 else "experimental"
    if hold <= 7 * 24 * 60:
        return "swing"
    return "high_conviction"


def calculate_derived_metrics(m: WalletMetrics, trades: list[TradeObservation] | None = None) -> WalletMetrics:
    trades = trades or []
    if trades:
        holds = [t.hold_minutes for t in trades if t.hold_minutes > 0]
        winners = [t.hold_minutes for t in trades if t.realized_pnl_usd > 0 and t.hold_minutes > 0]
        losers = [t.hold_minutes for t in trades if t.realized_pnl_usd <= 0 and t.hold_minutes > 0]
        if holds:
            m.avg_hold_minutes = mean(holds)
            m.hold_variance = pstdev(holds) ** 2 if len(holds) > 1 else 0.0
        if winners:
            m.winner_hold_minutes = mean(winners)
            m.winner_hold_variance = pstdev(winners) ** 2 if len(winners) > 1 else 0.0
        if losers:
            m.loser_hold_minutes = mean(losers)
            m.loser_hold_variance = pstdev(losers) ** 2 if len(losers) > 1 else 0.0
        comparable = [(t.hold_minutes, t.realized_pnl_usd > 0) for t in trades if t.hold_minutes > 0]
        if comparable:
            m.winner_longer_than_loser_rate = sum(
                1 for hold, win in comparable if (win and hold >= m.loser_hold_minutes) or (not win and hold <= m.winner_hold_minutes)
            ) / len(comparable)
        m.early_entry_rate = sum(1 for t in trades if t.launch_ts and t.entry_ts and t.entry_ts >= t.launch_ts and t.entry_ts - t.launch_ts <= 15 * 60) / max(len(trades), 1)
        m.early_actionable_rate = sum(1 for t in trades if t.actionable) / len(trades)
        m.transfer_in_count = sum(1 for t in trades if t.transfer_in)
        m.residual_hold_rate = sum(1 for t in trades if t.residual_hold) / len(trades)

    if m.trade_count_30d <= 0:
        m.trade_count_30d = len(trades)
    if m.hold_consistency <= 0 and m.avg_hold_minutes > 0:
        cv = coefficient_of_variation([t.hold_minutes for t in trades if t.hold_minutes > 0]) if trades else 1.0
        m.hold_consistency = max(0.0, min(1.0, 1.0 / (1.0 + cv)))

    m.pnl_7d_vs_30d_ratio = m.realized_pnl_7d / max(abs(m.realized_pnl_30d) / 4.0, 1e-9)
    m.recent_profit_stability = normalized_stability(m.daily_profit_series)
    if m.style is None:
        m.style = classify_style(m)
    return m


def divergence_label(m: WalletMetrics) -> str:
    ratio = m.pnl_7d_vs_30d_ratio
    if m.realized_pnl_30d > 0 and m.realized_pnl_7d > 0 and 0.50 <= ratio <= 1.50:
        return "strong_consistency"
    if ratio > 3.0:
        return "hot_streak"
    if m.realized_pnl_30d > 0 and m.realized_pnl_7d < 0:
        return "decaying"
    return "mixed"


def distribution_score(m: WalletMetrics) -> float:
    buckets = m.profit_buckets
    total = sum(buckets.values()) or 1
    small_medium = (buckets.get("0–2x", 0) + buckets.get("2–5x", 0)) / total
    lottery = buckets.get(">5x", 0) / total
    losses = (buckets.get("<-50%", 0) + buckets.get("-50%–0%", 0)) / total
    return max(0.0, min(1.0, 0.50 * small_medium + 0.30 * (1 - lottery) + 0.20 * (1 - losses)))


def actionability_score(m: WalletMetrics) -> float:
    entry = max(0.0, min(1.0, m.early_actionable_rate))
    conviction = max(0.0, min(1.0, m.current_conviction))
    style = max(0.0, min(1.0, m.style_match_score))
    crowding = max(0.0, min(1.0, m.crowding_score))
    return max(0.0, min(1.0, 0.35 * entry + 0.25 * conviction + 0.20 * style + 0.20 * (1 - crowding)))
