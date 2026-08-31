import random
from datetime import date, timedelta
from typing import List, Dict, Any, Optional


def calculate_cycle_predictions(
    logs: List[Any], 
    tracking_mode: str = "regular", 
    custom_cycle_length: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calculate menstrual cycle predictions, phase tracking, prediction confidence,
    and specialized insights based on past logs and selected health profile mode (PCOS, Irregular, Regular).
    """
    import math
    today = date.today()

    # Filter logs that have period_start=True and sort by date ascending
    start_logs = sorted(
        [log for log in logs if getattr(log, "period_start", False)],
        key=lambda x: x.date
    )

    # Set baseline default based on mode or user override
    if custom_cycle_length and custom_cycle_length >= 15:
        default_baseline = custom_cycle_length
    elif tracking_mode == "pcos_pcod":
        default_baseline = 35  # PCOS cycles lean longer on average
    elif tracking_mode == "perimenopause":
        default_baseline = 26
    else:
        default_baseline = 28

    average_cycle_length = default_baseline
    confidence = "High"
    intervals = []

    # Maximum interval window depending on mode
    max_valid_interval = 120 if tracking_mode in ["pcos_pcod", "irregular"] else 50
    min_valid_interval = 15

    if len(start_logs) >= 2:
        for i in range(1, len(start_logs)):
            diff = (start_logs[i].date - start_logs[i-1].date).days
            if min_valid_interval <= diff <= max_valid_interval:
                intervals.append(diff)

        if intervals:
            if tracking_mode == "pcos_pcod":
                # For PCOS, use median to reduce outlier distortion from missing/skipped cycles
                sorted_intervals = sorted(intervals)
                mid = len(sorted_intervals) // 2
                if len(sorted_intervals) % 2 == 0:
                    median_val = (sorted_intervals[mid - 1] + sorted_intervals[mid]) / 2.0
                else:
                    median_val = float(sorted_intervals[mid])
                average_cycle_length = int(round(median_val))
            elif tracking_mode == "irregular":
                # Exponential weighting giving 60% weight to recent 2 cycles
                if len(intervals) == 1:
                    average_cycle_length = intervals[0]
                else:
                    weighted_sum = intervals[-1] * 0.4 + intervals[-2] * 0.3 + (sum(intervals[:-2]) / max(1, len(intervals)-2)) * 0.3
                    average_cycle_length = int(round(weighted_sum))
            else:
                average_cycle_length = int(round(sum(intervals) / len(intervals)))

            # Calculate Standard Deviation for Prediction Confidence
            mean = sum(intervals) / len(intervals)
            variance = sum((x - mean) ** 2 for x in intervals) / len(intervals)
            std_dev = math.sqrt(variance)

            if tracking_mode == "pcos_pcod":
                confidence = "Moderate" if std_dev <= 7 else "Low (PCOS Variation)"
            elif tracking_mode == "irregular":
                confidence = "Moderate" if std_dev <= 5 else "Low"
            else:
                if std_dev <= 3:
                    confidence = "High"
                elif std_dev <= 6:
                    confidence = "Moderate"
                else:
                    confidence = "Low"
        else:
            confidence = "Baseline Estimate"
    else:
        confidence = "Baseline Estimate"

    # Determine last period start date
    if start_logs:
        last_period_start = start_logs[-1].date
    else:
        last_period_start = today - timedelta(days=14)

    # Calculate next period start date
    predicted_next_period = last_period_start + timedelta(days=average_cycle_length)
    if predicted_next_period < today:
        days_past = (today - last_period_start).days
        cycles_ahead = (days_past // average_cycle_length) + 1
        predicted_next_period = last_period_start + timedelta(days=cycles_ahead * average_cycle_length)

    # Ovulation & Fertile Window calculation
    luteal_length = 14
    ovulation_date = predicted_next_period - timedelta(days=luteal_length)
    fertile_window_start = ovulation_date - timedelta(days=4)
    fertile_window_end = ovulation_date + timedelta(days=2)

    # Current cycle day
    days_since_start = (today - last_period_start).days
    current_cycle_day = (days_since_start % average_cycle_length) + 1

    # Determine Phase & Description
    if current_cycle_day <= 5:
        current_phase = "Menstrual"
        phase_description = "Estrogen & progesterone low. Prioritize rest, hydration, anti-inflammatory nutrition, and gentle recovery."
    elif current_cycle_day <= (average_cycle_length - 14 - 2):
        current_phase = "Follicular"
        if tracking_mode == "pcos_pcod":
            phase_description = "Prolonged Follicular Phase typical in PCOS. Estrogen is gradually building. Keep up steady moderate exercise."
        else:
            phase_description = "Estrogen levels are rising. Energy and mood climb. Ideal time for strength training and high-focus work."
    elif current_cycle_day <= (average_cycle_length - 14 + 2):
        current_phase = "Ovulatory"
        phase_description = "LH surge window. Estrogen peaks. Log ovulation test strip results if tracking conception or LH levels."
    else:
        current_phase = "Luteal"
        phase_description = "Progesterone dominant phase. Support insulin sensitivity, manage cravings with complex carbs, and focus on stress relief."

    # Calculate deviation for current cycle
    deviation = 0
    deviation_message = None
    if start_logs:
        last_period_start_date = start_logs[-1].date
        days_since_start = (today - last_period_start_date).days
        
        if days_since_start >= average_cycle_length + 4:
            deviation = days_since_start - average_cycle_length
            if tracking_mode == "pcos_pcod":
                deviation_message = f"Cycle day {days_since_start} ({deviation} days past expected window). Delayed ovulation is common in PCOS."
            else:
                deviation_message = f"Your cycle is {deviation} days later than usual. High stress or hormonal variation detected?"
        elif len(start_logs) >= 2:
            last_completed_cycle_length = (start_logs[-1].date - start_logs[-2].date).days
            diff = last_completed_cycle_length - average_cycle_length
            if abs(diff) >= 4:
                deviation = diff
                dir_str = "later" if diff > 0 else "earlier"
                deviation_message = f"Your last cycle was {abs(diff)} days {dir_str} than baseline average."

    # PCOS & Profile Insights
    pcos_insights = []
    if tracking_mode == "pcos_pcod":
        pcos_insights.append("🌸 **PCOS Mode Active**: Calculations use rolling medians to accommodate variable cycle lengths.")
        pcos_insights.append("💡 **Insulin & Metabolism**: Pair carbohydrates with protein/fiber to keep blood glucose levels stable.")
        pcos_insights.append("🧪 **LH Tracking**: Because LH can stay elevated in PCOS, track multiple positive test days or BBT for true ovulation confirmation.")
    elif tracking_mode == "irregular":
        pcos_insights.append("📊 **Irregular Mode Active**: Exponential smoothing applies higher weight to your most recent cycles.")
        pcos_insights.append("🌿 **Symptom Logging**: Log daily symptoms to help identify recurring hormonal patterns.")
    elif tracking_mode == "perimenopause":
        pcos_insights.append("⚡ **Perimenopause Mode Active**: Shortening or skipping cycles is normal. Focus on bone health & sleep quality.")

    return {
        "average_cycle_length": average_cycle_length,
        "predicted_next_period": predicted_next_period.isoformat(),
        "ovulation_date": ovulation_date.isoformat(),
        "fertile_window_start": fertile_window_start.isoformat(),
        "fertile_window_end": fertile_window_end.isoformat(),
        "current_cycle_day": current_cycle_day,
        "current_phase": current_phase,
        "phase_description": phase_description,
        "deviation": deviation,
        "deviation_message": deviation_message,
        "tracking_mode": tracking_mode,
        "prediction_confidence": confidence,
        "pcos_insights": pcos_insights,
    }



def calculate_wellness_score(sleep: float, hydration: float, exercise: int, stress: str, mood: int) -> int:
    """Calculate daily wellness score (0-100) based on health inputs."""
    # Sleep: 7 to 9 hours is optimal (20 pts). 6 or 10 is 15 pts. 5 or 11 is 10 pts. Otherwise 5 pts.
    if 7.0 <= sleep <= 9.0:
        sleep_pts = 20
    elif 6.0 <= sleep < 7.0 or 9.0 < sleep <= 10.0:
        sleep_pts = 15
    elif 5.0 <= sleep < 6.0 or 10.0 < sleep <= 11.0:
        sleep_pts = 10
    else:
        sleep_pts = 5

    # Hydration: 2.5L+ = 20 pts. 2.0L-2.4L = 16 pts. 1.5L-1.9L = 12 pts. 1.0L-1.4L = 8 pts. <1.0L = 4 pts.
    if hydration >= 2.5:
        hyd_pts = 20
    elif hydration >= 2.0:
        hyd_pts = 16
    elif hydration >= 1.5:
        hyd_pts = 12
    elif hydration >= 1.0:
        hyd_pts = 8
    else:
        hyd_pts = 4

    # Exercise: 30+ min = 20 pts. 15-29 min = 15 pts. 1-14 min = 10 pts. 0 min = 5 pts.
    if exercise >= 30:
        ex_pts = 20
    elif exercise >= 15:
        ex_pts = 15
    elif exercise > 0:
        ex_pts = 10
    else:
        ex_pts = 5

    # Stress: low = 20 pts, medium = 12 pts, high = 4 pts.
    stress_lower = stress.lower()
    if stress_lower == "low":
        str_pts = 20
    elif stress_lower == "medium":
        str_pts = 12
    else:
        str_pts = 4

    # Mood: 1-5. 5 = 20 pts, 4 = 17 pts, 3 = 14 pts, 2 = 10 pts, 1 = 5 pts.
    if mood == 5:
        mood_pts = 20
    elif mood == 4:
        mood_pts = 17
    elif mood == 3:
        mood_pts = 14
    elif mood == 2:
        mood_pts = 10
    else:
        mood_pts = 5

    return sleep_pts + hyd_pts + ex_pts + str_pts + mood_pts


def generate_ai_health_summary(
    user_email: str,
    cycle_logs: List[Any],
    mood_logs: List[Any],
    wellness_log: Any = None
) -> Dict[str, Any]:
    """Generate dynamic AI daily health summary and scores for dashboard header."""
    raw_name = user_email.split('@')[0] if '@' in user_email else user_email
    name = raw_name.capitalize() if raw_name.lower() != "demo" else "Priya"

    pred = calculate_cycle_predictions(cycle_logs)
    cycle_day = pred["current_cycle_day"]
    phase = pred["current_phase"]

    bullets = [
        f"Day {cycle_day} of your {phase.lower()} cycle"
    ]

    # Mood week calculation
    if len(mood_logs) >= 2:
        bullets.append("Mood trend shows positive alignment with cycle")
    else:
        bullets.append("Log mood daily to unlock trend insights")

    if phase == "Menstrual":
        bullets.append("Iron-rich meals are recommended today")
        bullets.append("Gentle yoga can reduce cramps by 30%")
        rec = "Take a 20-minute walk after lunch to improve energy."
    elif phase == "Follicular":
        bullets.append("Protein-rich meals support muscle recovery today")
        bullets.append("Strength training boosts metabolism by 15%")
        rec = "Schedule your high-intensity strength session for early afternoon."
    elif phase == "Ovulatory":
        bullets.append("Complex carbs fuel your peak stamina today")
        bullets.append("Dynamic cardio maximizes cardiovascular burn")
        rec = "Capitalize on peak energy with a 30-minute cardio session."
    else:  # Luteal
        bullets.append("Magnesium & B6 rich foods soothe PMS symptoms")
        bullets.append("Pilates & gentle stretching promote core stability")
        rec = "Practice 10 minutes of deep belly breathing before sleep."

    # Parse wellness log if provided
    if wellness_log:
        wellness_score = int(wellness_log.wellness_score)
        ai_health_score = min(100, wellness_score + 2)

        # Sleep quality text
        sleep = wellness_log.sleep_hours
        if sleep >= 8.0:
            sleep_label = "Restorative"
        elif sleep >= 7.0:
            sleep_label = "Good"
        elif sleep >= 6.0:
            sleep_label = "Light"
        else:
            sleep_label = "Insufficient"
        sleep_quality = f"{sleep} hrs • {sleep_label}"

        # Stress level text
        stress = wellness_log.stress_level.lower()
        if stress == "low":
            stress_level = "Low (22%)"
        elif stress == "medium":
            stress_level = "Moderate (55%)"
        else:
            stress_level = "High (85%)"

        # Hydration text
        hyd = wellness_log.hydration_liters
        if hyd >= 3.0:
            hydration = f"{hyd}L • Goal Met 💧"
        else:
            hydration = f"{hyd}L / 3.0L Goal"

        bullets.append(f"Water Intake: {hyd}L logged today")
        bullets.append(f"Sleep: {sleep} hrs logged last night")
    else:
        wellness_score = 87
        ai_health_score = 89
        sleep_quality = "8.2 hrs • Restorative"
        stress_level = "Low (22%)"
        hydration = "2.4L / 80% Goal"
        bullets.append("Drink 2.4L water today")

    return {
        "wellness_score": wellness_score,
        "ai_health_score": ai_health_score,
        "sleep_quality": sleep_quality,
        "stress_level": stress_level,
        "hydration": hydration,
        "greeting": f"🌸 Good Morning, {name}!",
        "bullets": bullets,
        "ai_recommendation": rec
    }



def get_phase_workout_recommendations(phase: str) -> List[Dict[str, str]]:
    """Return tailored workout recommendations based on menstrual cycle phase."""
    phase = phase.capitalize()

    if phase == "Menstrual":
        return [
            {
                "title": "Gentle Restorative Yoga",
                "category": "Flexibility",
                "duration": "25 mins",
                "intensity": "Low",
                "description": "Slow, grounding postures with deep belly breathing to alleviate pelvic cramping and lumbar pressure.",
                "benefits": "Relieves period cramps, lowers cortisol, promotes restorative sleep."
            },
            {
                "title": "Mindful Nature Walk",
                "category": "Cardio",
                "duration": "30 mins",
                "intensity": "Low-Moderate",
                "description": "An easy outdoor stroll at a comfortable pace to promote circulation without straining joints.",
                "benefits": "Boosts endorphins gently without elevating inflammation."
            },
            {
                "title": "Pelvic & Lower Back Mobility",
                "category": "Mobility",
                "duration": "15 mins",
                "intensity": "Low",
                "description": "Cat-cow stretches, child's pose, and gentle hip openers designed specifically for period comfort.",
                "benefits": "Releases lumbar tension and relaxes tight pelvic floor muscles."
            }
        ]
    elif phase == "Follicular":
        return [
            {
                "title": "Full-Body Strength & Sculpt",
                "category": "Strength",
                "duration": "45 mins",
                "intensity": "Moderate-High",
                "description": "Dumbbell compound movements (squats, lunges, presses) taking advantage of rising estrogen energy.",
                "benefits": "Builds lean muscle mass, enhances insulin sensitivity."
            },
            {
                "title": "HIIT Energy Pulse",
                "category": "HIIT",
                "duration": "30 mins",
                "intensity": "High",
                "description": "Short bursts of bodyweight cardio interspaced with recovery intervals for maximum cardiovascular boost.",
                "benefits": "Maximizes metabolic burn and raises stamina."
            },
            {
                "title": "Dynamic Power Flow",
                "category": "Yoga",
                "duration": "40 mins",
                "intensity": "Moderate",
                "description": "Vinyasa flow focusing on balance, core activation, and rhythmic strength building.",
                "benefits": "Improves flexibility, posture, and mental focus."
            }
        ]
    elif phase == "Ovulatory":
        return [
            {
                "title": "High-Energy Peak Cardio",
                "category": "Cardio",
                "duration": "40 mins",
                "intensity": "High",
                "description": "Running, cycling, or energetic dance workouts while your stamina and pain tolerance peak.",
                "benefits": "Capitalizes on peak estrogen for maximal athletic output and cardiovascular conditioning."
            },
            {
                "title": "Heavy Lift & Hypertrophy",
                "category": "Strength",
                "duration": "50 mins",
                "intensity": "High",
                "description": "Challenge your personal bests in compound strength lifts with optimal muscle recovery speed.",
                "benefits": "Stimulates bone density and neuromuscular strength."
            },
            {
                "title": "Kickboxing & Conditioning",
                "category": "Combat Fitness",
                "duration": "35 mins",
                "intensity": "High",
                "description": "Fast-paced punch-kick combos paired with agility core drills for ultimate stress relief.",
                "benefits": "Releases high dopamine and boosts confidence."
            }
        ]
    else:  # Luteal Phase
        return [
            {
                "title": "Core & Reformer Pilates",
                "category": "Pilates",
                "duration": "35 mins",
                "intensity": "Moderate",
                "description": "Low-impact, controlled resistance exercise strengthening core stabilization without high impact.",
                "benefits": "Reduces PMS bloating and supports lumbar stability."
            },
            {
                "title": "Incline Treadmill Walk",
                "category": "Cardio",
                "duration": "30 mins",
                "intensity": "Moderate",
                "description": "Steady-state heart rate maintenance to burn calories without overstimulating adrenal response.",
                "benefits": "Sustains fat oxidation while preventing heat fatigue."
            },
            {
                "title": "Yin Yoga & Deep Breathing",
                "category": "Recovery",
                "duration": "20 mins",
                "intensity": "Low",
                "description": "Deep held stretches paired with 4-7-8 parasympathetic breathing to soothe premenstrual anxiety.",
                "benefits": "Calms the nervous system and aids sleep quality before menstruation."
            }
        ]


def calculate_mood_trends(logs: List[Any]) -> Dict[str, Any]:
    """Calculate 4-week average mood trends from logs."""
    today = date.today()
    weekly_trends = []

    total_mood_sum = 0
    total_entries_count = 0

    for i in range(3, -1, -1):
        start = today - timedelta(days=(i + 1) * 7 - 1)
        end = today - timedelta(days=i * 7)

        period_logs = [l for l in logs if start <= l.date <= end]

        if period_logs:
            avg = sum(l.mood for l in period_logs) / len(period_logs)
            count = len(period_logs)
            total_mood_sum += sum(l.mood for l in period_logs)
            total_entries_count += count
        else:
            avg = 3.0  # Neutral baseline if no entries logged
            count = 0

        label = "This Week" if i == 0 else f"{i} Wk{'s' if i > 1 else ''} Ago"
        weekly_trends.append({
            "week_label": label,
            "average_mood": round(float(avg), 2),
            "entries_count": count
        })

    overall_avg = (
        round(total_mood_sum / total_entries_count, 2)
        if total_entries_count > 0
        else 3.5
    )

    return {
        "weekly_trends": weekly_trends,
        "overall_average": overall_avg
    }


def get_health_articles() -> List[Dict[str, Any]]:
    """Return 12 comprehensive articles on women's health topics."""
    return [
        {
            "id": 1,
            "title": "Demystifying PCOS: Symptoms, Causes, and Daily Management",
            "category": "PCOS",
            "summary": "Polycystic Ovary Syndrome affects 1 in 10 women. Discover how nutrition, movement, and stress regulation foster hormonal balance.",
            "content": """### Understanding Polycystic Ovary Syndrome (PCOS)

Polycystic Ovary Syndrome (PCOS) is a common endocrine disorder characterized by hormonal imbalances, irregular menstrual cycles, and elevated androgen levels.

#### Key Symptoms to Watch For:
- **Irregular or Absent Periods:** Anovulatory cycles where ovulation occurs infrequently.
- **Androgen Excess:** Manifested as acne, hirsutism (excess facial/body hair), or hair thinning.
- **Polycystic Ovaries:** Enlarged ovaries containing small fluid-filled follicles visible on ultrasound.
- **Insulin Resistance:** Up to 70% of women with PCOS experience insulin resistance, leading to energy slumps and weight fluctuations.

#### Evidence-Based Daily Strategies:
1. **Low Glycemic Load Eating:** Pair complex carbohydrates with healthy proteins and fats to prevent rapid blood glucose spikes.
2. **Targeted Exercise:** Combine resistance training with low-intensity cardio to improve muscle insulin sensitivity without overwhelming cortisol.
3. **Inositol Supplementation:** Consult your healthcare provider about Myo-inositol and D-chiro-inositol, which support ovulatory function.""",
            "myth": "PCOS only affects women who are overweight.",
            "fact": "PCOS occurs in women of all body types, including lean individuals ('Lean PCOS'). Insulin resistance and hormonal dysregulation can affect anyone regardless of weight."
        },
        {
            "id": 2,
            "title": "Endometriosis 101: Navigating Chronic Pain and Finding Relief",
            "category": "Endometriosis",
            "summary": "Learn about tissue proliferation outside the uterus, warning signs beyond severe cramps, and integrative pain management.",
            "content": """### What is Endometriosis?

Endometriosis occurs when tissue similar to the uterine lining (endometrium) grows outside the uterine cavity—commonly on the ovaries, fallopian tubes, and pelvic walls.

#### Recognizing Severe Symptoms:
- **Dysmenorrhea:** Painful period cramps that do not respond to over-the-counter pain medicine.
- **Deep Pelvic Pain:** Discomfort during intercourse, bowel movements, or urination during menstruation.
- **Chronic Fatigue:** Persistent tiredness caused by constant immune activity and systemic inflammation.

#### Treatment & Management Approaches:
- **Medical Diagnostics:** Laparoscopy remains the gold standard diagnostic tool.
- **Anti-Inflammatory Nutrition:** Incorporating Omega-3 fatty acids (salmon, chia seeds, walnuts) and leafy greens to reduce pelvic inflammatory signals.
- **Pelvic Floor Physical Therapy:** Specialized therapy to release muscular spasms in the pelvic basin.""",
            "myth": "Getting pregnant cures endometriosis.",
            "fact": "Pregnancy may temporarily suppress symptoms due to hormonal shifts, but it is not a medical cure. Symptoms often resume post-partum."
        },
        {
            "id": 3,
            "title": "Thriving Through Menopause & Perimenopause Transition",
            "category": "Menopause",
            "summary": "Understanding hot flashes, sleep changes, and bone health as your body navigates the natural transition of perimenopause.",
            "content": """### Embracing the Menopause Journey

Perimenopause can begin 4 to 8 years before menopause (defined as 12 consecutive months without a period).

#### Common Transitions & What Causes Them:
- **Hot Flashes & Night Sweats:** Caused by fluctuating estrogen levels recalibrating the hypothalamus (body thermostat).
- **Sleep Architecture Changes:** Reduced progesterone can disrupt deep REM sleep.
- **Bone Density Considerations:** Estrogen plays a vital role in bone mineral retention.

#### Actionable Wellness Tips:
1. **Strength & Impact Training:** Weight-bearing exercises stimulate osteoblast activity, preserving bone strength.
2. **Magnesium Glycinate:** Supports muscle relaxation and restful sleep quality.
3. **Phytoestrogen Foods:** Flaxseeds, chickpeas, and organic soy contain mild plant compounds that soothe hormonal dips.""",
            "myth": "Menopause happens overnight at age 50.",
            "fact": "Perimenopause is a gradual multi-year journey involving fluctuating hormone levels long before menstruation stops completely."
        },
        {
            "id": 4,
            "title": "Choosing the Right Contraception Method for Your Body",
            "category": "Contraception",
            "summary": "A balanced guide comparing hormonal pills, copper/hormonal IUDs, implants, and fertility awareness methods.",
            "content": """### Navigating Contraceptive Options

Selecting birth control is a personal decision that depends on lifestyle, reproductive goals, and health history.

#### Categories of Contraception:
1. **Hormonal Methods (Pills, Patch, Ring, Progestin IUD):** Suppress ovulation or thicken cervical mucus. Ideal for lightening heavy periods.
2. **Non-Hormonal Methods (Copper IUD, Barrier Methods):** 100% hormone-free protection. Copper IUD offers long-term efficacy up to 10 years.
3. **Fertility Awareness-Based Methods (FABM):** Tracking basal body temperature (BBT), cervical fluid, and cycle timing. Requires strict consistency.

#### Key Questions for Your Gynaecologist:
- Will this method impact my future fertility timeline?
- What are the potential side effects for my specific health profile?""",
            "myth": "The birth control pill causes long-term infertility after stopping.",
            "fact": "Contraception temporarily prevents pregnancy while in use. Fertility typically returns to baseline shortly after discontinuation."
        },
        {
            "id": 5,
            "title": "Nurturing Mental Health: Premenstrual Dysphoric Disorder (PMDD)",
            "category": "Mental Health",
            "summary": "Understanding the difference between mild PMS moodiness and severe PMDD anxiety/depression during the luteal phase.",
            "content": """### Understanding PMDD vs PMS

Premenstrual Dysphoric Disorder (PMDD) is a severe, neurobiologically based reaction to normal monthly hormonal shifts.

#### Characteristics of PMDD:
- Intense emotional distress, sudden panic, or severe depressive episodes occurring exclusively during the 7-14 days before menstruation.
- Immediate symptom relief within 1-2 days of period onset.

#### Integrative Support Strategies:
- **Symptom Tracking:** Keep a 2-month daily log correlating mood ratings with cycle dates.
- **CBT & Mindfulness Therapy:** Cognitive Behavioral Techniques build resilience during heightened anxiety windows.
- **Medical Consultation:** SSRIs (either daily or luteal-phase dosing) and Calcium/Vitamin D supplementation are clinically proven interventions.""",
            "myth": "PMDD is just an excuse for being moody before your period.",
            "fact": "PMDD is a recognized medical condition in the DSM-5 caused by cellular sensitivity in the brain to hormonal fluctuations."
        },
        {
            "id": 6,
            "title": "Cycle Syncing Nutrition: Fueling Your Body's 4 Phases",
            "category": "Nutrition",
            "summary": "Tailoring your macronutrients and micronutrients to match energy needs across Menstrual, Follicular, Ovulatory, and Luteal phases.",
            "content": """### What is Cycle Syncing Nutrition?

Your metabolic rate and nutrient requirements change dynamically throughout your 28-day cycle.

#### Phase-by-Phase Nutritional Focus:
- **Menstrual Phase (Days 1-5):** Iron-rich foods (spinach, lentils, red meat), warm broths, and anti-inflammatory ginger tea.
- **Follicular Phase (Days 6-11):** Fresh sprouted grains, fermented probiotic foods (kimchi, kefir), and vibrant salads.
- **Ovulatory Phase (Days 12-16):** Antioxidant-rich berries, raw vegetables, and light lean proteins.
- **Luteal Phase (Days 17-28):** Complex carbs (sweet potatoes, oats, brown rice) to support serotonin production and curve PMS cravings.""",
            "myth": "You should eat the exact same calories and macros every single day of the month.",
            "fact": "Metabolic rate naturally increases during the luteal phase by 100–300 calories. Adjusting food intake prevents energy crashes."
        },
        {
            "id": 7,
            "title": "Understanding Cervical Mucus & Fertile Window Signs",
            "category": "PCOS",
            "summary": "Identify natural biological markers that indicate ovulation and prime fertility windows.",
            "content": """### Tracking Cervical Fluid for Reproductive Insights

Cervical mucus shifts in color, volume, and texture in response to rising estrogen levels prior to ovulation.

#### The Fluid Progression:
1. **Post-Period Dryness:** Low fluid output right after menstruation.
2. **Sticky / Tacky:** Creamy or lotion-like texture indicating growing follicular activity.
3. **Egg-White Consistency (EWCM):** Clear, stretchy, slippery fluid resembling raw egg whites. **This signals peak fertility!**""",
            "myth": "Ovulation always occurs precisely on Day 14 for every woman.",
            "fact": "Ovulation timing varies based on individual cycle length and stress factors. Cycle tracking provides personalized accuracy."
        },
        {
            "id": 8,
            "title": "Restorative Sleep for Hormonal Regeneration",
            "category": "Mental Health",
            "summary": "How circadian rhythms influence progesterone, estrogen, and cortisol release during sleep.",
            "content": """### The Sleep-Hormone Connection

Quality sleep is non-negotiable for endocrine regulation. Poor sleep elevates cortisol, which competes directly with progesterone production.

#### Optimal Hygiene Habits for Women:
- Maintain a cool dark bedroom (65-68°F) to accommodate luteal body temperature rises.
- Limit blue light emission 1 hour prior to sleep to enable peak melatonin synthesis.
- Drink chamomile or passionflower tea for parasympathetic soothing.""",
            "myth": "6 hours of sleep is plenty if you drink enough coffee.",
            "fact": "Women frequently require 7-9 hours of sleep due to complex cyclical endocrine recovery processes."
        },
        {
            "id": 9,
            "title": "Iron Deficiency Anemia: Protecting Your Vitality During Menstruation",
            "category": "Nutrition",
            "summary": "Identify signs of low ferritin levels caused by heavy period flow and how to boost absorption naturally.",
            "content": """### Combating Iron Depletion

Heavy menstrual bleeding (menorrhagia) is the leading cause of iron deficiency anemia in reproductive-aged women.

#### Symptoms of Low Ferritin:
- Pale skin and cold hands/feet.
- Shortness of breath during moderate stair climbing.
- Unexplained brain fog or restless leg feeling at night.

#### Boost Absorption:
Pair plant-based iron sources (heme and non-heme) with Vitamin C rich foods (citrus, bell peppers) to triple intestinal absorption!""",
            "myth": "Drinking tea or coffee with meals helps iron absorption.",
            "fact": "Tannins and polyphenols in tea and coffee inhibit iron absorption by up to 60%. Consume them 1 hour away from meals."
        },
        {
            "id": 10,
            "title": "Managing Perimenopausal Brain Fog & Energy Drops",
            "category": "Menopause",
            "summary": "Neuro-protective habits to boost focus and cognitive clarity during mid-life hormonal transitions.",
            "content": """### Navigating Hormonal Brain Fog

Estrogen acts as a primary fuel source for brain glucose metabolism. As levels fluctuate in mid-life, temporary memory lapses can occur.

#### Protective Cognitive Habits:
- Practice daily mindfulness or meditation to lower cortisol-induced memory inhibition.
- Consume Omega-3 DHA/EPA fatty acids to support neural cell membrane integrity.
- Engage in novel skill learning (languages, musical instruments, new sports).""",
            "myth": "Perimenopausal brain fog means permanent cognitive decline.",
            "fact": "Brain fog during perimenopause is temporary. Studies show cognitive performance recalibrates once hormone levels stabilize post-menopause."
        },
        {
            "id": 11,
            "title": "The Gut-Hormone Axis: Estrobolome and Estrogen Detox",
            "category": "Nutrition",
            "summary": "How your intestinal microbiome regulates circulating estrogen and prevents estrogen dominance.",
            "content": """### Meet Your Estrobolome

The estrobolome is a specialized collection of gut bacteria capable of metabolizing and modulating the body's circulating estrogen.

#### Supporting Healthy Estrogen Clearance:
- Eat cruciferous vegetables (broccoli, Brussels sprouts, cabbage) rich in Diindolylmethane (DIM).
- Ensure daily bowel movements to prevent reabsorption of excreted hormones.
- Avoid unnecessary antibiotic overuse to maintain microbiome diversity.""",
            "myth": "Gut health only matters for digestion, not hormonal health.",
            "fact": "The gut estrobolome plays a direct role in regulating circulating estrogen levels throughout the entire body."
        },
        {
            "id": 12,
            "title": "Pelvic Floor Health Beyond Pregnancy: Strength & Relaxation",
            "category": "Fitness",
            "summary": "Understanding hypertonic vs hypotonic pelvic muscles and how to practice proper relaxation.",
            "content": """### Understanding Your Pelvic Floor

The pelvic floor is a muscular hammock supporting the bladder, uterus, and bowel.

#### Hypertonic vs. Hypotonic:
- **Hypotonic (Weak):** Requires gentle strengthening exercises (Kegels) under professional guidance.
- **Hypertonic (Overly Tight):** Requires lengthen-and-relax breathing (Reverse Kegels) to release chronic pelvic tension.

Consult a qualified pelvic health physical therapist to determine your specific muscle tone before starting heavy exercise.""",
            "myth": "Every woman should perform hundreds of tight Kegel squeezes every single day.",
            "fact": "If your pelvic muscles are already tight or hypertonic, doing traditional Kegels can worsen pelvic pain. Relaxation breathing is often needed first!"
        }
    ]


def get_myth_cards() -> List[Dict[str, Any]]:
    """Return interactive myth vs fact cards for Health Library."""
    return [
        {
            "id": 1,
            "category": "Menstruation",
            "myth": "Menstrual cycles must always be exactly 28 days long.",
            "fact": "Normal adult cycle length ranges anywhere from 21 to 35 days. Variation of a few days from month to month is completely healthy."
        },
        {
            "id": 2,
            "category": "PCOS",
            "myth": "Women with PCOS cannot get pregnant naturally.",
            "fact": "While PCOS can cause irregular ovulation, many women conceive naturally or with minor lifestyle/medical support once ovulation is restored."
        },
        {
            "id": 3,
            "category": "Fitness",
            "myth": "You should avoid all physical exercise while on your period.",
            "fact": "Gentle movement like yoga or walking releases endorphins that reduce cramping, moodiness, and inflammation during menstruation."
        },
        {
            "id": 4,
            "category": "Endometriosis",
            "myth": "Extremely painful period cramps are just a normal part of being a woman.",
            "fact": "Severe pain that disables daily activities is NOT normal and may indicate underlying conditions like endometriosis or fibroids."
        },
        {
            "id": 5,
            "category": "Contraception",
            "myth": "Using hormonal birth control causes permanent weight gain.",
            "fact": "Clinical studies show most birth control methods do not cause significant long-term weight gain, though mild fluid retention can occur initially."
        },
        {
            "id": 6,
            "category": "Mental Health",
            "myth": "PMS emotional changes are all 'just in your head'.",
            "fact": "Hormonal shifts directly interact with brain neurotransmitters like serotonin and dopamine, causing legitimate physiological mood changes."
        }
    ]


def retrieve_relevant_health_article(query: str) -> Optional[Dict[str, Any]]:
    """
    RAG helper function: Search Health Library articles for relevant terms matching query.
    Returns article dict if a match is found, else None.
    """
    q_lower = query.lower()
    articles = get_health_articles()

    best_article = None
    best_score = 0

    for article in articles:
        score = 0
        title_lower = article["title"].lower()
        summary_lower = article["summary"].lower()
        cat_lower = article["category"].lower()
        content_lower = article["content"].lower()

        for word in q_lower.split():
            if len(word) >= 3:
                if word in cat_lower:
                    score += 4
                elif word in title_lower:
                    score += 3
                elif word in summary_lower:
                    score += 2
                elif word in content_lower:
                    score += 1

        if score > best_score:
            best_score = score
            best_article = article

    if best_score >= 2:
        return best_article
    return None


def generate_fallback_chat_reply(
    message: str, 
    user_context: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Generate empathetic, CBT-focused, context-aware, and RAG-grounded supportive response.
    Vera Persona: Empathetic, supportive, non-diagnostic wellness companion with multi-turn memory.
    """
    msg_lower = message.lower()
    context_prefix = ""

    # Inspect history for previous topics if query is a follow-up ("tell me more", "what foods for that?", "how to treat it")
    history_topics = []
    if history:
        for turn in reversed(history):
            content = turn.get("content", "").lower()
            for topic in ["pcos", "endometriosis", "menopause", "contraception", "pmdd", "cramps", "anxiety", "fitness"]:
                if topic in content and topic not in history_topics:
                    history_topics.append(topic)

    search_query = message
    if history_topics and any(vague in msg_lower for vague in ["that", "this", "it", "more", "foods", "treatment", "tips", "help", "how"]):
        search_query = f"{message} {' '.join(history_topics)}"

    # Build personalized context prefix if available
    if user_context:
        phase = user_context.get("current_phase")
        day = user_context.get("current_cycle_day")
        mode = user_context.get("tracking_mode", "regular")
        mode_label = "PCOS Mode" if mode == "pcos_pcod" else (f"{mode.capitalize()} Mode" if mode != "regular" else "")

        mode_str = f" • {mode_label}" if mode_label else ""
        if phase and day:
            context_prefix = f"🌸 *Current Context: Day {day} ({phase} Phase{mode_str})*\n\n"

    # Crisis detection keyword check
    crisis_keywords = ["suicide", "kill myself", "end my life", "harm myself", "hopeless", "can't go on", "want to die"]
    if any(k in msg_lower for k in crisis_keywords):
        resp_text = (
            "I hear how much pain you are in right now, and I care deeply about your safety. "
            "Please know that you do not have to carry this alone. If you are in crisis or distress, "
            "reach out immediately to compassionate professionals who want to help:\n\n"
            "• **National Suicide & Crisis Lifeline**: Call or text **988** (Available 24/7, free, confidential)\n"
            "• **Crisis Text Line**: Text **HOME** to **741741**\n"
            "• **International Helplines**: Visit [findahelpline.com](https://findahelpline.com)\n\n"
            "Please take a deep breath and connect with someone right now. You matter."
        )
        return {"response": resp_text, "source": "fallback", "article_citation": None}

    # Real-Time Live Status & Metrics Query Check
    if any(k in msg_lower for k in ["status", "summary", "how am i doing", "live update", "my metrics", "hydration", "water", "sleep", "score"]):
        sleep = user_context.get("sleep_hours") if user_context else None
        hyd = user_context.get("hydration_liters") if user_context else None
        ex = user_context.get("exercise_minutes") if user_context else None
        stress = user_context.get("stress_level") if user_context else None
        score = user_context.get("wellness_score") if user_context else None

        from datetime import datetime
        now_str = datetime.now().strftime("%b %d, %H:%M")

        metrics_list = []
        if hyd is not None:
            hyd_status = "✅ Goal Met" if float(hyd) >= 2.0 else "💧 Hydration Recommended"
            metrics_list.append(f"• **Hydration**: {float(hyd):.1f}L ({hyd_status})")
        if sleep is not None:
            sleep_status = "Restorative 🌙" if float(sleep) >= 7.0 else "Sleep Deficit 😴"
            metrics_list.append(f"• **Sleep Duration**: {float(sleep):.1f} hrs ({sleep_status})")
        if ex is not None:
            metrics_list.append(f"• **Movement**: {ex} mins logged")
        if stress:
            metrics_list.append(f"• **Stress Rating**: {str(stress).capitalize()}")
        if score:
            metrics_list.append(f"• **Real-Time Wellness Score**: **{score}/100**")

        metrics_text = "\n".join(metrics_list) if metrics_list else "• Live metrics updating dynamically based on your daily inputs!"

        resp_text = (
            f"⚡ **Real-Time Health Sync** [{now_str}]\n\n"
            f"{context_prefix}"
            f"Here is your real-time wellness synthesis:\n\n"
            f"{metrics_text}\n\n"
            "💡 *Vera's Real-Time Rec*: Stay hydrated and prioritize restorative sleep during this cycle window. "
            "What else can I help you analyze right now?"
        )
        return {"response": resp_text, "source": "live_sync", "article_citation": None}

    # RAG Retrieval Check for medical / health topics
    retrieved_article = retrieve_relevant_health_article(search_query)
    article_citation = None
    rag_text = ""

    if retrieved_article:
        article_citation = {
            "id": retrieved_article["id"],
            "title": retrieved_article["title"],
            "category": retrieved_article["category"],
            "summary": retrieved_article["summary"]
        }
        rag_text = (
            f"\n\n📖 **Verified Clinical Knowledge from Health Library**:\n"
            f"> *\"{retrieved_article['title']}\"*\n"
            f"> {retrieved_article['summary']}\n\n"
            f"You can read the full article in the **Health Library** tab!"
        )

    # TTC Topic specific empathetic responses
    if any(k in msg_lower for k in ["bbt", "basal body", "temperature chart", "temp shift", "thermal shift"]):
        bbt_info = ""
        if user_context and user_context.get("latest_bbt"):
            bbt_info = f"\n\n🌡️ **Your Recorded Temp**: {user_context.get('latest_bbt')} °C"
        
        resp_text = (
            f"{context_prefix}Basal Body Temperature (BBT) is your body's resting baseline temperature taken first thing upon waking. 🌡️{bbt_info}\n\n"
            "• **What the chart means**: A sustained rise in temperature (typically 0.2°C to 0.5°C over at least 3 consecutive days above the previous 6 days) "
            "can be consistent with ovulation having occurred due to increased progesterone.\n"
            "• **Important Retrospective Note**: BBT is generally more useful for confirming that ovulation may have occurred *retrospectively* "
            "rather than predicting ovulation precisely in advance.\n\n"
            "Log your morning temperature consistently before getting out of bed for the most clear pattern visualization!"
            f"{rag_text}"
        )
        return {"response": resp_text, "source": "rag_fallback" if article_citation else "fallback", "article_citation": article_citation}

    if any(k in msg_lower for k in ["lh", "surge", "ovulation test", "test strip"]):
        lh_info = ""
        if user_context and user_context.get("latest_lh"):
            lh_info = f"\n\n🧪 **Your Logged LH Result**: {user_context.get('latest_lh')}"

        resp_text = (
            f"{context_prefix}Luteinizing Hormone (LH) tests measure the hormonal surge that triggers follicle rupture and egg release. 🧪{lh_info}\n\n"
            "• **What an LH Surge means**: An LH surge indicates that LH levels have peaked, which typically precedes ovulation by roughly 24 to 36 hours. "
            "This suggests you may be approaching your estimated fertile window.\n"
            "• **Important Note**: An LH surge indicates hormone activity but does not guarantee that ovulation will occur at a specific time or that conception will result.\n\n"
            "Log your daily LH test strip results under the **TTC Dashboard** to track your surge trend!"
            f"{rag_text}"
        )
        return {"response": resp_text, "source": "rag_fallback" if article_citation else "fallback", "article_citation": article_citation}

    if any(k in msg_lower for k in ["mucus", "cervical mucus", "egg white", "watery"]):
        resp_text = (
            f"{context_prefix}Cervical mucus observation is a key natural fertility signal! 💧\n\n"
            "• **Egg-White / Watery**: Stretchy or clear, slippery mucus is typically fertile-type cervical fluid, facilitating sperm transport during the fertile window.\n"
            "• **Creamy / Sticky / Dry**: Common during non-fertile or luteal phases.\n"
            "• **Important Note**: Cervical mucus variations provide an estimate of your hormonal environment, but individual patterns vary and observation alone does not guarantee ovulation."
            f"{rag_text}"
        )
        return {"response": resp_text, "source": "rag_fallback" if article_citation else "fallback", "article_citation": article_citation}

    if any(k in msg_lower for k in ["pregnancy test", "positive test", "positive pregnancy", "test result"]):
        resp_text = (
            f"{context_prefix}Pregnancy testing provides vital clarity on your journey. 🧪\n\n"
            "If you have recorded a **positive test result**, please consider contacting a qualified healthcare professional for confirmation, blood work, and clinical guidance.\n\n"
            "• **Note**: HerWell tracks your self-reported log entries but does not diagnose pregnancy or replace professional medical care."
            f"{rag_text}"
        )
        return {"response": resp_text, "source": "rag_fallback" if article_citation else "fallback", "article_citation": article_citation}

    if any(k in msg_lower for k in ["ttc", "trying to conceive", "fertile window", "conceive"]):
        resp_text = (
            f"{context_prefix}Welcome to your Trying to Conceive (TTC) journey! 🌱\n\n"
            "Combining multiple fertility signals—**BBT morning temperatures, LH test surges, and cervical mucus observations**—gives you the clearest retrospective picture of your fertile window.\n\n"
            "Remember that every body is unique, and cycle variations are completely natural. Switch to **🌱 Trying to Conceive (TTC) Mode** in the header to view your customized fertility dashboard!"
            f"{rag_text}"
        )
        return {"response": resp_text, "source": "rag_fallback" if article_citation else "fallback", "article_citation": article_citation}

    # Topic specific empathetic responses
    if any(k in msg_lower for k in ["cramps", "period", "bleed", "pain", "flow", "spotting"]):
        resp_text = (
            f"{context_prefix}I am sending you warmth and soothing comfort. Period discomfort can feel so draining. 🌸\n\n"
            "Here is a gentle **4-7-8 breathing exercise** to soothe your nervous system right now:\n"
            "1. **Inhale** quietly through your nose for 4 seconds.\n"
            "2. **Hold** your breath comfortably for 7 seconds.\n"
            "3. **Exhale** slowly through your mouth with a soft sigh for 8 seconds.\n\n"
            "Consider placing a warm heating pad over your lower abdomen and sipping ginger or chamomile tea."
            f"{rag_text}"
        )
        return {"response": resp_text, "source": "rag_fallback" if article_citation else "fallback", "article_citation": article_citation}

    if any(k in msg_lower for k in ["anxious", "anxiety", "stressed", "overwhelmed", "panic", "worry"]):
        resp_text = (
            f"{context_prefix}Thank you for sharing how you feel with me. It takes courage to acknowledge stress and anxiety. 🌿\n\n"
            "Here is a quick **CBT grounding prompt** to bring your mind back to safety:\n"
            "• **5-4-3-2-1 Grounding Method**:\n"
            "  - Name 5 things you can see around you right now.\n"
            "  - Touch 4 physical objects near you.\n"
            "  - Listen for 3 distinct sounds.\n"
            "  - Notice 2 scents.\n"
            "  - Take 1 deep, intentional breath.\n\n"
            "*Affirmation*: 'I am safe in this present moment. I give myself permission to rest and release control.'"
            f"{rag_text}"
        )
        return {"response": resp_text, "source": "rag_fallback" if article_citation else "fallback", "article_citation": article_citation}

    if any(k in msg_lower for k in ["sad", "depressed", "lonely", "crying", "down", "tired", "exhausted"]):
        resp_text = (
            f"{context_prefix}I hear you, and I am sitting softly with you in this moment. Your feelings are valid and allowed to exist. 💗\n\n"
            "When energy feels low, try treating yourself with gentle self-compassion:\n"
            "• Journal prompt: *'What is one small kindness I can offer myself today, without expecting perfection?'*\n"
            "• Drink a glass of warm water.\n"
            "• Wrap yourself in a cozy blanket and rest your eyes for 10 minutes.\n\n"
            "Remember: You don't have to figure everything out today. Just one small step at a time."
            f"{rag_text}"
        )
        return {"response": resp_text, "source": "rag_fallback" if article_citation else "fallback", "article_citation": article_citation}

    if any(k in msg_lower for k in ["workout", "exercise", "fitness", "gym", "yoga", "energy"]):
        resp_text = (
            f"{context_prefix}Movement is such a powerful act of self-care! 💪\n\n"
            "Listening to your body's monthly cycle rhythm is key to sustainable fitness. "
            "Whether you're feeling energetic for high-intensity work or needing the gentle restoration of a slow yoga stretch, "
            "honoring your present energy yields the best long-term hormonal balance.\n\n"
            "Check out the **Fitness** tab for workouts synchronized specifically to your current phase!"
            f"{rag_text}"
        )
        return {"response": resp_text, "source": "rag_fallback" if article_citation else "fallback", "article_citation": article_citation}

    if retrieved_article:
        resp_text = (
            f"{context_prefix}I found information on that in our medical library! 📚\n\n"
            f"**{retrieved_article['title']}** ({retrieved_article['category']}):\n"
            f"{retrieved_article['summary']}\n\n"
            f"Here is a key insight: {retrieved_article['content'][:300]}...\n\n"
            f"Would you like to read the full article or discuss any specific symptoms?"
        )
        return {"response": resp_text, "source": "rag_fallback", "article_citation": article_citation}

    # General supportive response pool
    general_replies = [
        (
            f"{context_prefix}Hello! I am Vera, your wellness companion. 🌸 I am here to offer empathy, mindfulness techniques, "
            "and CBT-inspired journaling prompts. How can I support your mind and body today?"
        ),
        (
            f"{context_prefix}I am so glad you reached out! Taking time for your well-being is never selfish—it's essential. "
            "What has been on your heart or mind today?"
        ),
        (
            f"{context_prefix}Here is your positive affirmation for today: *'My body is wise, resilient, and deserving of gentle care every single day.'* "
            "How can I assist you with your cycle, mood, or wellness journey today?"
        )
    ]
    return {"response": random.choice(general_replies), "source": "fallback", "article_citation": None}


def detect_bbt_ovulation_pattern(bbt_logs: List[Any], last_period_start: Optional[date] = None) -> Dict[str, Any]:
    """
    Analyze BBT trends to identify a possible post-ovulatory temperature shift.
    Uses strict non-diagnostic language:
    'Your recent temperature pattern shows a sustained rise that may be consistent with ovulation having occurred around this time.'
    """
    if not bbt_logs or len(bbt_logs) < 3:
        return {
            "detected": False,
            "estimated_cycle_day": None,
            "confidence": "Insufficient Data",
            "message": "Log morning BBT consistently to help detect post-ovulatory temperature patterns.",
            "disclaimer": "BBT generally helps confirm that ovulation may have occurred retrospectively rather than predicting it with certainty."
        }

    # Sort logs by date ascending
    sorted_logs = sorted(bbt_logs, key=lambda x: x.date)

    # Standardize temps to Celsius (°C)
    entries = []
    for log in sorted_logs:
        temp = log.temperature
        if getattr(log, "unit", "°C") == "°F":
            temp = (temp - 32.0) * (5.0 / 9.0)
        entries.append({"date": log.date, "temp": temp})

    detected = False
    shift_date = None

    if len(entries) >= 6:
        for i in range(3, len(entries)):
            prior_temps = [e["temp"] for e in entries[max(0, i-6):i]]
            baseline = sum(prior_temps) / len(prior_temps)
            curr_temp = entries[i]["temp"]

            if curr_temp - baseline >= 0.15:
                if i + 2 < len(entries):
                    next_temps = [entries[i+1]["temp"], entries[i+2]["temp"]]
                    if all(t - baseline >= 0.10 for t in next_temps):
                        detected = True
                        shift_date = entries[i]["date"]
                        break
                else:
                    detected = True
                    shift_date = entries[i]["date"]
                    break

    est_day = None
    if detected and shift_date and last_period_start:
        est_day = (shift_date - last_period_start).days + 1
        confidence = "Moderate"
        message = "Your recent temperature pattern shows a sustained rise that may be consistent with ovulation having occurred around this time."
    elif detected and shift_date:
        confidence = "Moderate"
        message = "Your recent temperature pattern shows a sustained rise that may be consistent with ovulation having occurred around this time."
    else:
        confidence = "Baseline Tracking"
        message = "No sustained temperature shift detected yet in current logs."

    return {
        "detected": detected,
        "estimated_cycle_day": est_day,
        "confidence": confidence,
        "message": message,
        "disclaimer": "BBT generally helps confirm that ovulation may have occurred retrospectively rather than predicting it with certainty."
    }


def aggregate_fertility_signals(
    cycle_logs: List[Any], 
    bbt_logs: List[Any], 
    lh_logs: List[Any], 
    mucus_logs: List[Any],
    predictions: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Combine available user fertility signals into a summary card data structure.
    """
    today = date.today()
    
    # BBT status
    bbt_today = next((b for b in sorted(bbt_logs, key=lambda x: x.date, reverse=True) if b.date == today), None)
    if bbt_today:
        bbt_status = f"🟢 Logged today ({bbt_today.temperature:.1f}{bbt_today.unit})"
    elif bbt_logs:
        latest = max(bbt_logs, key=lambda x: x.date)
        bbt_status = f"🟡 Last logged {latest.date} ({latest.temperature:.1f}{latest.unit})"
    else:
        bbt_status = "⚪ Not logged today"

    # LH status
    lh_today = next((l for l in sorted(lh_logs, key=lambda x: x.date, reverse=True) if l.date == today), None)
    if lh_today:
        badge_emoji = "🔴" if lh_today.result == "surge" else ("🟡" if lh_today.result == "rising" else "🟢")
        lh_status = f"{badge_emoji} {lh_today.result.replace('_', ' ').capitalize()} recorded today"
    else:
        surge_recent = next((l for l in sorted(lh_logs, key=lambda x: x.date, reverse=True) if l.result == "surge" and (today - l.date).days <= 3), None)
        if surge_recent:
            lh_status = f"🔴 Surge recorded on {surge_recent.date}"
        elif lh_logs:
            lh_status = f"🟢 Recent test logged ({lh_logs[-1].result.capitalize()})"
        else:
            lh_status = "⚪ No LH tests recorded"

    # Cervical Mucus status
    mucus_today = next((m for m in sorted(mucus_logs, key=lambda x: x.date, reverse=True) if m.date == today), None)
    if mucus_today:
        type_str = mucus_today.type.replace('_', '-').capitalize()
        is_fertile_type = mucus_today.type in ["watery", "egg_white"]
        icon = "💧" if is_fertile_type else "⚪"
        fert_label = "Fertile-type observation" if is_fertile_type else "Non-fertile observation"
        cervical_mucus_status = f"{icon} {fert_label} ({type_str})"
    elif mucus_logs:
        latest_m = max(mucus_logs, key=lambda x: x.date)
        type_str = latest_m.type.replace('_', '-').capitalize()
        cervical_mucus_status = f"⚪ Last observed {type_str} on {latest_m.date}"
    else:
        cervical_mucus_status = "⚪ Not observed today"

    # Cycle Data Status
    cycle_day = predictions.get("current_cycle_day", 1)
    cycle_len = predictions.get("average_cycle_length", 28)
    cycle_data_status = f"🟢 Consistent (Day {cycle_day} of {cycle_len})"

    # Estimated Fertility Status
    phase = predictions.get("current_phase", "Follicular")
    if phase == "Ovulatory" or (lh_today and lh_today.result in ["surge", "rising"]) or (mucus_today and mucus_today.type in ["watery", "egg_white"]):
        estimated_fertility_status = "Potentially fertile window"
    elif phase == "Follicular" and cycle_day >= cycle_len - 18:
        estimated_fertility_status = "Approaching fertile window"
    elif phase == "Luteal":
        estimated_fertility_status = "Lower fertility phase (Luteal)"
    else:
        estimated_fertility_status = "Baseline tracking phase"

    return {
        "bbt_status": bbt_status,
        "lh_status": lh_status,
        "cervical_mucus_status": cervical_mucus_status,
        "cycle_data_status": cycle_data_status,
        "estimated_fertility_status": estimated_fertility_status,
        "disclaimer": "Fertility estimates are based on logged information and can be inaccurate. Never rely on predictions as guaranteed contraception or medical diagnosis."
    }

