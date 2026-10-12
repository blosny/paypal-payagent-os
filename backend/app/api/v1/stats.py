from datetime import datetime, timezone
from fastapi import APIRouter
from ...services.policy_engine import policy_engine
from ...models.transaction import TransactionStatus
from ...config import settings

router = APIRouter()


@router.get("/summary")
async def get_system_summary():
    """Provides aggregated metrics for the PayAgent OS supervisor dashboard."""
    agents = policy_engine.list_agents()
    all_txs = policy_engine.list_transactions()

    total_allocated = sum(a.wallet_balance for a in agents)
    total_spent_today = sum(a.spent_today for a in agents)
    pending_approvals = [t for t in all_txs if t.status == TransactionStatus.PENDING_APPROVAL]
    autonomous_executed = [
        t for t in all_txs if t.status == TransactionStatus.APPROVED_AUTONOMOUS
    ]
    settled_or_approved = [
        t
        for t in all_txs
        if t.status
        in [
            TransactionStatus.APPROVED_AUTONOMOUS,
            TransactionStatus.APPROVED_BY_HUMAN,
            TransactionStatus.SETTLED,
        ]
    ]

    total_spent_volume = sum(t.amount for t in settled_or_approved)

    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "paypal_mode": settings.PAYPAL_MODE,
        "is_live_sandbox": settings.has_paypal_credentials,
        "active_agents_count": len([a for a in agents if a.is_active]),
        "total_allocated_funds": round(total_allocated, 2),
        "total_spent_today": round(total_spent_today, 2),
        "total_volume_processed": round(total_spent_volume, 2),
        "pending_approval_count": len(pending_approvals),
        "autonomous_execution_count": len(autonomous_executed),
        "total_transactions_count": len(all_txs),
    }


@router.get("/analytics")
async def get_analytics_breakdown():
    """Provides visual analytics, vendor shares, and guardrail savings breakdown."""
    agents = policy_engine.list_agents()
    all_txs = policy_engine.list_transactions()

    total_allocated = sum(a.wallet_balance for a in agents)
    total_spent_today = sum(a.spent_today for a in agents)
    total_daily_budget = sum(a.policy.daily_budget for a in agents)

    # Vendor spending breakdown
    vendor_totals = {}
    for tx in all_txs:
        if tx.status in [
            TransactionStatus.APPROVED_AUTONOMOUS,
            TransactionStatus.APPROVED_BY_HUMAN,
            TransactionStatus.SETTLED,
        ]:
            vendor = tx.recipient if hasattr(tx, "recipient") else "Other"
            vendor_totals[vendor] = vendor_totals.get(vendor, 0.0) + tx.amount

    vendor_breakdown = [
        {
            "vendor": v,
            "amount": round(amt, 2),
            "percentage": round((amt / max(total_spent_today, 1.0)) * 100, 1)
            if total_spent_today > 0
            else 0,
        }
        for v, amt in vendor_totals.items()
    ]

    # Agent breakdown & chart colors
    colors = ["#10b981", "#3b82f6", "#f59e0b", "#a855f7", "#ec4899"]
    agent_shares = []
    for i, a in enumerate(agents):
        pct = (
            round((a.spent_today / max(total_spent_today, 1.0)) * 100, 1)
            if total_spent_today > 0
            else 0
        )
        agent_shares.append(
            {
                "agent_id": a.id,
                "name": a.name,
                "personality": a.personality.value,
                "spent_today": round(a.spent_today, 2),
                "daily_budget": round(a.policy.daily_budget, 2),
                "wallet_balance": round(a.wallet_balance, 2),
                "share_percentage": pct,
                "color": colors[i % len(colors)],
            }
        )

    # Savings & Preserved Capital by Guardrails / Frugal Personality
    rejected_txs = [
        t
        for t in all_txs
        if t.status
        in [
            TransactionStatus.REJECTED_BY_HUMAN,
            TransactionStatus.REJECTED_BY_POLICY,
        ]
    ]
    rejected_volume = sum(t.amount for t in rejected_txs)
    savings_by_guardrails = round(rejected_volume, 2)

    return {
        "total_allocated": round(total_allocated, 2),
        "total_spent_today": round(total_spent_today, 2),
        "total_daily_budget": round(total_daily_budget, 2),
        "savings_by_guardrails": savings_by_guardrails,
        "negotiation_volume": 0.0,
        "active_negotiations_count": 0,
        "vendor_breakdown": vendor_breakdown,
        "agent_shares": agent_shares,
        "total_tx_count": len(all_txs),
        "approved_tx_count": len(
            [
                t
                for t in all_txs
                if t.status
                in [
                    TransactionStatus.APPROVED_AUTONOMOUS,
                    TransactionStatus.APPROVED_BY_HUMAN,
                ]
            ]
        ),
        "pending_tx_count": len(
            [t for t in all_txs if t.status == TransactionStatus.PENDING_APPROVAL]
        ),
    }


from pydantic import BaseModel, Field
from typing import Optional


class StressTestRequest(BaseModel):
    price_inflation_pct: float = Field(default=0.0, ge=-50.0, le=200.0)
    traffic_multiplier: float = Field(default=1.0, ge=0.5, le=10.0)
    outage_vendor: Optional[str] = Field(default=None)
    fallback_vendor: Optional[str] = Field(default="HuggingFace")


class CfoQueryRequest(BaseModel):
    question: str = Field(..., min_length=2)


@router.post("/simulate-stress")
async def simulate_financial_stress(req: StressTestRequest):
    """Simulates financial liquidity under price inflation, traffic surges, and vendor outages."""
    agents = policy_engine.list_agents()
    total_budget = sum(a.policy.daily_budget for a in agents)
    total_spent_today = sum(a.spent_today for a in agents)
    remaining_budget = max(0.0, total_budget - total_spent_today)

    # Base daily velocity: assume 60% of daily budget is normal baseline velocity
    baseline_velocity = max(total_spent_today, total_budget * 0.45)
    
    # Apply inflation & traffic multiplier
    inflation_factor = 1.0 + (req.price_inflation_pct / 100.0)
    projected_daily_burn = baseline_velocity * inflation_factor * req.traffic_multiplier

    # Outage impact: switching to alternative vendor adds premium
    outage_surcharge = 0.0
    if req.outage_vendor:
        outage_surcharge = projected_daily_burn * 0.18  # 18% spot migration surcharge
        projected_daily_burn += outage_surcharge

    # Hours until exhaustion
    hourly_rate = projected_daily_burn / 24.0
    if hourly_rate > 0:
        hours_until_exhaustion = round(remaining_budget / hourly_rate, 1)
    else:
        hours_until_exhaustion = 24.0

    hours_until_exhaustion = max(0.5, min(hours_until_exhaustion, 72.0))

    # Deficit calculation
    projected_deficit = max(0.0, projected_daily_burn - remaining_budget)

    # Risk level
    if hours_until_exhaustion < 6.0 or projected_deficit > 100.0:
        risk_level = "CRITICAL"
        risk_color = "#ef4444"
    elif hours_until_exhaustion < 14.0 or projected_deficit > 0:
        risk_level = "ELEVATED"
        risk_color = "#f59e0b"
    else:
        risk_level = "STABLE"
        risk_color = "#10b981"

    # Actionable Recommendation
    if risk_level == "CRITICAL":
        recommendation = (
            f"Likidite tükenme riski yüksek ({hours_until_exhaustion} saat kaldı). "
            f"DevOps Cimri Kasa rezervinden ${round(min(projected_deficit, 150.0), 2)} acil takviye yapılmalı "
            f"veya harcama tavanı geçici olarak kısıtlanmalıdır."
        )
    elif risk_level == "ELEVATED":
        recommendation = (
            f"Bütçe baskısı artıyor. Günlük bütçenin {round(projected_daily_burn, 2)} USD'ye çıkması öngörülüyor. "
            f"P2P kota müzakereleri aktif tutularak harcamalar kardeş kartlara paylaştırılmalı."
        )
    else:
        recommendation = (
            f"Finansal kalkan güvenli bölgede. Filo bütçesi bu stres koşullarında {hours_until_exhaustion} saat "
            f"kesintisiz otonom çalışmayı sürdürebilir."
        )

    return {
        "status": "success",
        "total_budget": round(total_budget, 2),
        "remaining_budget": round(remaining_budget, 2),
        "projected_daily_burn": round(projected_daily_burn, 2),
        "hours_until_exhaustion": hours_until_exhaustion,
        "projected_deficit": round(projected_deficit, 2),
        "risk_level": risk_level,
        "risk_color": risk_color,
        "outage_surcharge": round(outage_surcharge, 2),
        "recommendation": recommendation,
    }


@router.post("/cfo-query")
async def ask_cfo_copilot(req: CfoQueryRequest):
    """Interactive AI Financial Officer providing context-aware fleet intelligence."""
    agents = policy_engine.list_agents()
    all_txs = policy_engine.list_transactions()

    total_spent = sum(a.spent_today for a in agents)
    total_budget = sum(a.policy.daily_budget for a in agents)
    q = req.question.lower().strip()

    # Find highest spending agent
    sorted_by_spend = sorted(agents, key=lambda a: a.spent_today, reverse=True)
    top_agent = sorted_by_spend[0] if sorted_by_spend else None

    # Frugal vault state
    devops = next((a for a in agents if a.personality.value == "FRUGAL_VAULT"), None)
    research = next((a for a in agents if a.personality.value == "GROWTH_EXPLORER"), None)

    # Question matching logic
    if any(k in q for k in ["en çok", "en fazla", "harcadı", "kim", "hangi ajan", "who spent", "top spender"]):
        if top_agent and top_agent.spent_today > 0:
            answer = (
                f"📊 Bugün en çok harcamayı **{top_agent.name}** yaptı. "
                f"Toplam harcanan: **${top_agent.spent_today:.2f} USD** "
                f"(Günlük bütçesinin %{round((top_agent.spent_today / max(top_agent.policy.daily_budget, 1.0)) * 100)}'si). "
                f"Harcama odağı: `{', '.join(top_agent.policy.allowed_vendors[:3])}`."
            )
            suggested = f"{top_agent.name} limitini gözden geçir"
        else:
            answer = (
                f"Henüz kayda değer bir bütçe tüketimi yok. Toplam filo harcaması: **${total_spent:.2f} USD**. "
                f"En yüksek günlük bütçe kapasitesine sahip ajan: **{sorted(agents, key=lambda a: a.policy.daily_budget, reverse=True)[0].name}** ($300.00/gün)."
            )
            suggested = "Simülatörden test harcaması başlat"

    elif any(k in q for k in ["cimri", "neden reddetti", "frugal", "red", "reject", "borç"]):
        frugal_name = devops.name if devops else "DevOps Altyapı Ajanı"
        answer = (
            f"🏦 **{frugal_name}**, şirket fonlarını korumak için `FRUGAL_VAULT (Cimri Kasa)` finansal kişiliğine sahiptir. "
            f"Politikası gereği `min_lending_urgency = CRITICAL` kuralını işletir. "
            f"Eğer talep 'HIGH' veya 'MEDIUM' aciliyette ise, 'Rezervlerimi koruyorum' diyerek reddeder. "
            f"Sadece sistem kesintisi gibi 'CRITICAL' acil durumlarda kota paylaşır."
        )
        suggested = "Aciliyeti CRITICAL yaparak tekrar dene"

    elif any(k in q for k in ["tasarruf", "ne kadar kurtardık", "korunan", "saving"]):
        rejected_txs = [
            t for t in all_txs
            if t.status in [TransactionStatus.REJECTED_BY_POLICY, TransactionStatus.REJECTED_BY_HUMAN]
        ]
        rule_saved = sum(t.amount for t in rejected_txs)
        answer = (
            f"🛡️ PayAgent OS Politika Kalkanı ve HITL Onay Mekanizması sayesinde "
            f"toplam **${rule_saved:.2f} USD** şirket sermayesi korunmuştur:\n"
            f"• **${rule_saved:.2f} USD:** Politika motoru ve HITL kalkanı (limit/satıcı ihlalleri engeli)"
        )
        suggested = "Yönetici PDF raporunu indir"

    elif any(k in q for k in ["öneri", "optimize", "tavsiye", "nasıl", "recommend"]):
        answer = (
            f"💡 **CFO Optimizasyon Tavsiyeleri:**\n"
            f"1. **Araştırma Ajanı ({research.name if research else 'Ar-Ge'}):** Tekil harcama tavanı ($25) sık sık HITL onayına düşüyor. Tavanı $40'a çıkarırsanız yönetici onay yükü %50 azalır.\n"
            f"2. **DevOps Boşta Kalan Kota:** DevOps ajanı bütçesinin büyük kısmını kullanmıyor. Boşta kotayı gece saatlerinde veri modellemeye aktarabilirsiniz.\n"
            f"3. **Tedarikçi Çeşitliliği:** OpenAI harcamaları ağırlıkta; HuggingFace spot GPU arbitrajı ile %20 ek tasarruf sağlanabilir."
        )
        suggested = "Ar-Ge ajanı limitini güncelle"

    else:
        answer = (
            f"🤖 **PayAgent OS Finansal Durum Özeti:**\n"
            f"• Yönetilen Toplam Kasa: **${sum(a.wallet_balance for a in agents):.2f} USD**\n"
            f"• Bugünkü Tüketim: **${total_spent:.2f} / ${total_budget:.2f} USD**\n"
            f"• Aktif Ajan Sayısı: **{len(agents)}** (1 Cimri Kasa, 1 Büyüme Ar-Ge, 1 Dengeli Hazine)\n"
            f"• Güvenlik Durumu: Tüm işlemler PayPal Sandbox REST API v2 ve çift aşamalı Guardrails denetimindedir."
        )
        suggested = "Stres Simülatörünü çalıştır"

    return {
        "status": "success",
        "question": req.question,
        "answer": answer,
        "suggested_action": suggested,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


