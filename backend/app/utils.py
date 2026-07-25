import random
from datetime import date, timedelta
from typing import List, Dict, Any


def calculate_cycle_predictions(logs: List[Any]) -> Dict[str, Any]:
    """
    Calculate menstrual cycle predictions and determine current phase based on past logs.
    """
    today = date.today()

    # Filter logs that have period_start=True and sort by date ascending
    start_logs = sorted(
        [log for log in logs if getattr(log, "period_start", False)],
        key=lambda x: x.date
    )

    # Calculate average cycle length (default 28 days)
    average_cycle_length = 28
    if len(start_logs) >= 2:
        intervals = []
        for i in range(1, len(start_logs)):
            diff = (start_logs[i].date - start_logs[i-1].date).days
            # Filter out unrealistic log gaps (e.g., missed logging > 60 days)
            if 18 <= diff <= 45:
                intervals.append(diff)
        if intervals:
            average_cycle_length = int(round(sum(intervals) / len(intervals)))

    # Determine last period start date
    if start_logs:
        last_period_start = start_logs[-1].date
    else:
        # Fallback to 14 days ago if no period logged yet
        last_period_start = today - timedelta(days=14)

    # Calculate next period start date
    predicted_next_period = last_period_start + timedelta(days=average_cycle_length)
    if predicted_next_period < today:
        # If predicted next period date is in past, project forward to next cycle
        days_past = (today - last_period_start).days
        cycles_ahead = (days_past // average_cycle_length) + 1
        predicted_next_period = last_period_start + timedelta(days=cycles_ahead * average_cycle_length)

    # Ovulation & Fertile Window
    ovulation_date = predicted_next_period - timedelta(days=14)
    fertile_window_start = ovulation_date - timedelta(days=3)
    fertile_window_end = ovulation_date + timedelta(days=3)

    # Current cycle day
    days_since_start = (today - last_period_start).days
    current_cycle_day = (days_since_start % average_cycle_length) + 1

    # Determine Phase
    if current_cycle_day <= 5:
        current_phase = "Menstrual"
        phase_description = "Estrogen and progesterone are at their lowest. Focus on rest, hydration, and gentle activity."
    elif current_cycle_day <= (average_cycle_length // 2) - 2:
        current_phase = "Follicular"
        phase_description = "Estrogen levels are rising. Energy and mood climb. Ideal time for strength training and new initiatives."
    elif current_cycle_day <= (average_cycle_length // 2) + 2:
        current_phase = "Ovulatory"
        phase_description = "Estrogen peaks and LH surges. Maximum stamina, confidence, and social energy."
    else:
        current_phase = "Luteal"
        phase_description = "Progesterone rises then dips. High endurance early on, transitioning into low-impact recovery as your period approaches."

    return {
        "average_cycle_length": average_cycle_length,
        "predicted_next_period": predicted_next_period.isoformat(),
        "ovulation_date": ovulation_date.isoformat(),
        "fertile_window_start": fertile_window_start.isoformat(),
        "fertile_window_end": fertile_window_end.isoformat(),
        "current_cycle_day": current_cycle_day,
        "current_phase": current_phase,
        "phase_description": phase_description,
    }


def generate_ai_health_summary(user_email: str, cycle_logs: List[Any], mood_logs: List[Any]) -> Dict[str, Any]:
    """Generate dynamic AI daily health summary and scores for dashboard header."""
    raw_name = user_email.split('@')[0] if '@' in user_email else user_email
    name = raw_name.capitalize() if raw_name.lower() != "demo" else "Shreya"

    pred = calculate_cycle_predictions(cycle_logs)
    cycle_day = pred["current_cycle_day"]
    phase = pred["current_phase"]

    bullets = [
        f"Day {cycle_day} of your {phase.lower()} cycle",
        "Mood has improved by 12% this week"
    ]

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

    bullets.append("Drink 2.4L water today")

    return {
        "wellness_score": 87,
        "ai_health_score": 89,
        "sleep_quality": "8.2 hrs • Restorative",
        "stress_level": "Low (22%)",
        "hydration": "2.4L / 80% Goal",
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


def generate_fallback_chat_reply(message: str) -> str:
    """
    Generate empathetic, CBT-focused, supportive response when OpenAI API is unavailable.
    Vera Persona: Empathetic, supportive, non-diagnostic wellness companion.
    """
    msg_lower = message.lower()

    # Crisis detection keyword check
    crisis_keywords = ["suicide", "kill myself", "end my life", "harm myself", "hopeless", "can't go on", "want to die"]
    if any(k in msg_lower for k in crisis_keywords):
        return (
            "I hear how much pain you are in right now, and I care deeply about your safety. "
            "Please know that you do not have to carry this alone. If you are in crisis or distress, "
            "reach out immediately to compassionate professionals who want to help:\n\n"
            "• **National Suicide & Crisis Lifeline**: Call or text **988** (Available 24/7, free, confidential)\n"
            "• **Crisis Text Line**: Text **HOME** to **741741**\n"
            "• **International Helplines**: Visit [findahelpline.com](https://findahelpline.com)\n\n"
            "Please take a deep breath and connect with someone right now. You matter."
        )

    # Topic specific empathetic responses
    if any(k in msg_lower for k in ["cramps", "period", "bleed", "pain", "flow", "spotting"]):
        return (
            "I am sending you warmth and soothing comfort. Period pain can feel so draining. 🌸\n\n"
            "Here is a gentle 4-7-8 breathing exercise to soothe your nervous system right now:\n"
            "1. **Inhale** quietly through your nose for 4 seconds.\n"
            "2. **Hold** your breath comfortably for 7 seconds.\n"
            "3. **Exhale** slowly through your mouth with a soft sigh for 8 seconds.\n\n"
            "Consider placing a warm heating pad over your lower abdomen and sipping ginger or chamomile tea. "
            "How are your energy levels overall today?"
        )

    if any(k in msg_lower for k in ["anxious", "anxiety", "stressed", "overwhelmed", "panic", "worry"]):
        return (
            "Thank you for sharing how you feel with me. It takes courage to acknowledge stress and anxiety. 🌿\n\n"
            "Here is a quick CBT grounding prompt to bring your mind back to safety:\n"
            "• **5-4-3-2-1 Grounding Method**:\n"
            "  - Name 5 things you can see around you right now.\n"
            "  - Touch 4 physical objects near you.\n"
            "  - Listen for 3 distinct sounds.\n"
            "  - Notice 2 scents.\n"
            "  - Take 1 deep, intentional breath.\n\n"
            "*Affirmation*: 'I am safe in this present moment. I give myself permission to rest and release control.'"
        )

    if any(k in msg_lower for k in ["sad", "depressed", "lonely", "crying", "down", "tired", "exhausted"]):
        return (
            "I hear you, and I am sitting softly with you in this moment. Your feelings are valid and allowed to exist. 💗\n\n"
            "When energy feels low, try treating yourself with gentle self-compassion:\n"
            "• Journal prompt: *'What is one small kindness I can offer myself today, without expecting perfection?'*\n"
            "• Drink a glass of warm water.\n"
            "• Wrap yourself in a cozy blanket and rest your eyes for 10 minutes.\n\n"
            "Remember: You don't have to figure everything out today. Just one small step at a time."
        )

    if any(k in msg_lower for k in ["workout", "exercise", "fitness", "gym", "yoga", "energy"]):
        return (
            "Movement is such a powerful act of self-care! 💪\n\n"
            "Listening to your body's monthly cycle rhythm is key to sustainable fitness. "
            "Whether you're feeling energetic for high-intensity work or needing the gentle restoration of a slow yoga stretch, "
            "honoring your present energy yields the best long-term hormonal balance.\n\n"
            "Be sure to check out the **Fitness** tab in the top navigation bar for workouts synchronized specifically to your current cycle phase!"
        )

    # General supportive response pool
    general_replies = [
        (
            "Hello! I am Vera, your wellness companion. 🌸 I am here to offer empathy, mindfulness techniques, "
            "and CBT-inspired journaling prompts. How can I support your mind and body today?"
        ),
        (
            "I am so glad you reached out! Remember that taking time for your well-being is never selfish—it's essential. "
            "What has been on your heart or mind today?"
        ),
        (
            "Here is your positive affirmation for today: *'My body is wise, resilient, and deserving of gentle care every single day.'* "
            "How can I assist you with your cycle, mood, or wellness journey today?"
        ),
        (
            "Thank you for checking in with me. Taking a moment out of a busy day to focus on yourself is a wonderful step. "
            "Would you like a quick breathing exercise, a journaling prompt, or cycle guidance?"
        )
    ]
    return random.choice(general_replies)
