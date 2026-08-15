from src.wallet_screener.cluster_analysis import FundingObservation, analyze_cluster


def test_no_funding_is_independent():
    report = analyze_cluster("A", [], wallet_universe=["A", "B"])
    assert report.cluster_size == 1
    assert report.independence_score == 1.0


def test_shared_funder_links_wallets():
    observations = [
        FundingObservation("A", "F1", 1000),
        FundingObservation("B", "F1", 1050),
        FundingObservation("C", "F2", 2000),
    ]
    report = analyze_cluster("A", observations, wallet_universe=["A", "B", "C"])
    assert report.common_funder_count == 1
    assert report.linked_wallets == ["B"]
    assert report.cluster_size == 2
    assert report.synchronized_links == 1
    assert report.independence_score < 1.0


def test_multiple_funders_penalize_independence():
    observations = [
        FundingObservation("A", "F1", 1000),
        FundingObservation("A", "F2", 2000),
    ]
    report = analyze_cluster("A", observations, wallet_universe=["A"])
    assert report.common_funder_count == 2
    assert report.independence_score == 0.6
