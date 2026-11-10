"""Catalog of solution formats with transparent complexity baselines.

Baselines are product heuristics (AI_INTERPRETATION when used in scoring),
not measured market data. Prefer simpler formats when evidence is equal.
"""

from __future__ import annotations

from packages.contracts.formats import ComplexityLevel, FormatProfile, SolutionFormat

FORMAT_CATALOG: dict[SolutionFormat, FormatProfile] = {
    SolutionFormat.CALCULATOR_TOOL: FormatProfile(
        format=SolutionFormat.CALCULATOR_TOOL,
        label="Calculator / tool",
        complexity=ComplexityLevel.LOW,
        maintenance=ComplexityLevel.LOW,
        monetization_hypotheses=[
            "Lead capture",
            "Affiliate / freemium upgrade",
            "Usage-based API later",
        ],
        cheapest_validation="Ship a single static/interactive calculator landing page and measure completion + email capture.",
        default_preference_rank=1,
    ),
    SolutionFormat.NEWSLETTER_ALERTS: FormatProfile(
        format=SolutionFormat.NEWSLETTER_ALERTS,
        label="Newsletter / alerts",
        complexity=ComplexityLevel.LOW,
        maintenance=ComplexityLevel.MEDIUM,
        monetization_hypotheses=["Paid subscription", "Sponsorships"],
        cheapest_validation="Manual weekly digest to a waitlist; track open/reply intent.",
        default_preference_rank=2,
    ),
    SolutionFormat.SEO_WEBSITE_BLOG: FormatProfile(
        format=SolutionFormat.SEO_WEBSITE_BLOG,
        label="SEO website / blog",
        complexity=ComplexityLevel.MEDIUM,
        maintenance=ComplexityLevel.MEDIUM,
        monetization_hypotheses=["Ads", "Affiliate", "Lead gen into services/SaaS"],
        cheapest_validation="Publish 3 intent-matched articles; track organic impressions/clicks (no invented volumes).",
        default_preference_rank=3,
    ),
    SolutionFormat.YOUTUBE: FormatProfile(
        format=SolutionFormat.YOUTUBE,
        label="YouTube",
        complexity=ComplexityLevel.MEDIUM,
        maintenance=ComplexityLevel.MEDIUM,
        monetization_hypotheses=["Ads", "Sponsorships", "Course funnel"],
        cheapest_validation="Publish 2–3 explainers addressing top pain points; track retention comments.",
        default_preference_rank=4,
    ),
    SolutionFormat.DIRECTORY: FormatProfile(
        format=SolutionFormat.DIRECTORY,
        label="Directory",
        complexity=ComplexityLevel.MEDIUM,
        maintenance=ComplexityLevel.MEDIUM,
        monetization_hypotheses=["Featured listings", "Lead referrals"],
        cheapest_validation="Curate a spreadsheet/Notion directory of 30 entries; gauge inbound requests.",
        default_preference_rank=5,
    ),
    SolutionFormat.DIGITAL_PRODUCT: FormatProfile(
        format=SolutionFormat.DIGITAL_PRODUCT,
        label="Digital product (template/ebook/pack)",
        complexity=ComplexityLevel.LOW,
        maintenance=ComplexityLevel.LOW,
        monetization_hypotheses=["One-time purchase", "Bundle upsells"],
        cheapest_validation="Pre-sell a template pack with a landing page before building more.",
        default_preference_rank=6,
    ),
    SolutionFormat.WEB_APP: FormatProfile(
        format=SolutionFormat.WEB_APP,
        label="Web app",
        complexity=ComplexityLevel.HIGH,
        maintenance=ComplexityLevel.HIGH,
        monetization_hypotheses=["Freemium", "Subscription"],
        cheapest_validation="Clickable prototype solving one pain flow; 5 user interviews.",
        default_preference_rank=7,
    ),
    SolutionFormat.SAAS: FormatProfile(
        format=SolutionFormat.SAAS,
        label="SaaS",
        complexity=ComplexityLevel.HIGH,
        maintenance=ComplexityLevel.HIGH,
        monetization_hypotheses=["Subscription", "Usage pricing"],
        cheapest_validation="Concierge MVP / wizard-of-oz workflow before building billing.",
        default_preference_rank=8,
    ),
    SolutionFormat.API_DATA_SERVICE: FormatProfile(
        format=SolutionFormat.API_DATA_SERVICE,
        label="API / data service",
        complexity=ComplexityLevel.HIGH,
        maintenance=ComplexityLevel.HIGH,
        monetization_hypotheses=["API keys / usage tiers"],
        cheapest_validation="Deliver data via spreadsheet/email to 3 design partners first.",
        default_preference_rank=9,
    ),
    SolutionFormat.MARKETPLACE: FormatProfile(
        format=SolutionFormat.MARKETPLACE,
        label="Marketplace",
        complexity=ComplexityLevel.VERY_HIGH,
        maintenance=ComplexityLevel.VERY_HIGH,
        monetization_hypotheses=["Take rate", "Featured placement"],
        cheapest_validation="Manually match 5 buyers/sellers; do not build two-sided software yet.",
        default_preference_rank=10,
    ),
    SolutionFormat.AI_AGENT: FormatProfile(
        format=SolutionFormat.AI_AGENT,
        label="AI agent / automation",
        complexity=ComplexityLevel.HIGH,
        maintenance=ComplexityLevel.HIGH,
        monetization_hypotheses=["Subscription", "Per-run fees"],
        cheapest_validation="Human-in-the-loop script for one workflow; measure time saved.",
        default_preference_rank=11,
    ),
    SolutionFormat.ANDROID_APP: FormatProfile(
        format=SolutionFormat.ANDROID_APP,
        label="Android app",
        complexity=ComplexityLevel.VERY_HIGH,
        maintenance=ComplexityLevel.HIGH,
        monetization_hypotheses=["IAP", "Subscription", "Ads"],
        cheapest_validation="Validate mobile-only need via web MVP + mobile analytics intent surveys.",
        default_preference_rank=12,
    ),
    SolutionFormat.IOS_APP: FormatProfile(
        format=SolutionFormat.IOS_APP,
        label="iOS app",
        complexity=ComplexityLevel.VERY_HIGH,
        maintenance=ComplexityLevel.HIGH,
        monetization_hypotheses=["IAP", "Subscription"],
        cheapest_validation="Same as Android — prove mobile-only necessity before native build.",
        default_preference_rank=13,
    ),
    SolutionFormat.PROFESSIONAL_SERVICES: FormatProfile(
        format=SolutionFormat.PROFESSIONAL_SERVICES,
        label="Professional services",
        complexity=ComplexityLevel.MEDIUM,
        maintenance=ComplexityLevel.MEDIUM,
        monetization_hypotheses=["Project fees", "Retainer"],
        cheapest_validation="Sell a fixed-scope pilot service to 1–2 customers.",
        default_preference_rank=14,
    ),
}


def all_formats() -> list[FormatProfile]:
    return sorted(FORMAT_CATALOG.values(), key=lambda p: p.default_preference_rank)
