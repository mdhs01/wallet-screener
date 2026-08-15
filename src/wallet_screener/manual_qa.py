from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median

from .models import TradeObservation


@dataclass(slots=True)
class ManualQAReport:
    """Automated preparation/validation for the article's 15–20 trade manual sample.

    This module does not pretend to replace human review. It verifies that the
    sample is sufficiently complete and exposes the trade-level evidence that a
    reviewer needs before a wallet can advance.
    """

    sampled_count: int = 0
    sample_ready: bool = False
    complete_data_rate: float = 0.0
    actionable_rate: float = 0.0
    transfer_in_rate: float = 0.0
    early_entry_rate: float = 0.0
    median_entry_latency_minutes: float = 0.0
    repeatable_behavior_rate: float = 0.0
    partial_tp_rate: float = 0.0
    residual_hold_rate: float = 0.0
    cut_loss_rate: float = 0.0
    accumulate_rate: float = 0.0
    warnings: list[str] = field(default_factory=list)
    failed_checks: list[str] = field(default_factory=list)
    reviewer_prompts: list[str] = field(default_factory=list)

    @property
    def score(self) -> float:
        """Evidence-readiness score; not a replacement for the final wallet score."""
        if self.sampled_count == 0:
            return 0.0
        values = (
            self.complete_data_rate,
            self.actionable_rate,
            self.early_entry_rate,
            self.repeatable_behavior_rate,
        )
        return round(sum(values) / len(values), 4)


def _behavior_signature(trade: TradeObservation) -> tuple[bool, bool, bool, bool]:
    return (
        trade.partial_tp,
        trade.residual_hold,
        trade.cut_loss,
        trade.accumulate_underwater,
    )


def build_manual_qa_report(
    trades: list[TradeObservation],
    *,
    min_sample: int = 15,
    max_sample: int = 20,
    min_actionable_rate: float = 0.50,
    max_transfer_in_rate: float = 0.20,
    max_latency_minutes: float = 10.0,
    min_repeatable_behavior_rate: float = 0.50,
    min_complete_data_rate: float = 0.90,
) -> ManualQAReport:
    sample = trades[:max_sample]
    report = ManualQAReport(sampled_count=len(sample))

    if len(sample) < min_sample:
        report.failed_checks.append("manual_trade_sample_insufficient")
    else:
        report.sample_ready = True

    if not sample:
        report.failed_checks.append("manual_trade_sample_empty")
        return report

    complete = 0
    actionable = 0
    transfers = 0
    early = 0
    partial_tp = 0
    residual = 0
    cut_loss = 0
    accumulate = 0
    latencies: list[float] = []
    signatures: dict[tuple[bool, bool, bool, bool], int] = {}

    for trade in sample:
        core_complete = (
            trade.launch_ts is not None
            and trade.entry_ts is not None
            and trade.buy_size_usd > 0
            and trade.liquidity_at_entry_usd > 0
        )
        complete += int(core_complete)

        actionable += int(trade.actionable)
        transfers += int(trade.transfer_in)
        partial_tp += int(trade.partial_tp)
        residual += int(trade.residual_hold)
        cut_loss += int(trade.cut_loss)
        accumulate += int(trade.accumulate_underwater)

        if trade.entry_latency_minutes is not None:
            latencies.append(trade.entry_latency_minutes)
            early += int(trade.entry_latency_minutes <= max_latency_minutes)

        signature = _behavior_signature(trade)
        signatures[signature] = signatures.get(signature, 0) + 1

    n = len(sample)
    report.complete_data_rate = complete / n
    report.actionable_rate = actionable / n
    report.transfer_in_rate = transfers / n
    report.partial_tp_rate = partial_tp / n
    report.residual_hold_rate = residual / n
    report.cut_loss_rate = cut_loss / n
    report.accumulate_rate = accumulate / n

    if latencies:
        report.median_entry_latency_minutes = median(latencies)
        report.early_entry_rate = early / n
    else:
        report.failed_checks.append("entry_timing_data_missing")

    if signatures:
        repeatable_events = sum(count for count in signatures.values() if count >= 2)
        report.repeatable_behavior_rate = repeatable_events / n

    if report.complete_data_rate < min_complete_data_rate:
        report.failed_checks.append("trade_data_incomplete")
    if report.actionable_rate < min_actionable_rate:
        report.failed_checks.append("manual_actionability_below_min")
    if report.transfer_in_rate > max_transfer_in_rate:
        report.failed_checks.append("manual_transfer_in_rate_too_high")
    if latencies and report.median_entry_latency_minutes > max_latency_minutes:
        report.warnings.append("median_entry_latency_above_target")
    if report.repeatable_behavior_rate < min_repeatable_behavior_rate:
        report.warnings.append("behavior_pattern_repeatability_weak")

    # These prompts preserve the article's requested manual verification scope.
    report.reviewer_prompts.extend(
        [
            "Verify launch time versus actual entry time for each sampled trade.",
            "Verify entry size and liquidity at entry are representative of the wallet's normal execution.",
            "Check whether the trade was a real market entry or transfer-in / did-not-buy activity.",
            "Check hold duration, partial TP, residual hold, cut-loss and accumulate behavior.",
            "Confirm the sample behavior matches the aggregate wallet metrics rather than a cherry-picked subset.",
        ]
    )

    return report
