using System;
using System.Text;
using UnityEngine;

namespace DirtTrail
{
    /// <summary>What a single air was worth, once it survived the landing.</summary>
    public readonly struct TrickAward
    {
        public readonly string Label;
        public readonly int Points;
        public readonly int Combo;
        public readonly LandingQuality Landing;

        /// <summary>Whole rotations completed, so the shout can match the size.</summary>
        public readonly int Rotations;

        public TrickAward(string label, int points, int combo, LandingQuality landing,
                          int rotations)
        {
            Label = label;
            Points = points;
            Combo = combo;
            Landing = landing;
            Rotations = rotations;
        }
    }

    /// <summary>
    /// Rotation, airtime and landing quality turned into a score. Points are
    /// pending while you are in the air and are only banked when you ride away
    /// from it - crashing costs you the whole air, which is the entire reason
    /// to hold a flip open or shut it down early.
    /// </summary>
    public class TrickSystem : MonoBehaviour
    {
        [SerializeField] BikeController bike;

        [Header("Scoring")]
        [Tooltip("Points for the first rotation. Each further rotation in the same air scales up.")]
        [SerializeField] int flipBase = 100;

        [Tooltip("Airtime below this earns nothing. Small hops should not pay.")]
        [SerializeField] float minPaidAir = 1.1f;

        [SerializeField] int airBonusPerHalfSecond = 25;
        [SerializeField] int airBonusCap = 300;

        [Header("Multipliers")]
        [SerializeField] float perfectBonus = 1.5f;
        [SerializeField] float cleanBonus = 1.25f;
        [SerializeField] float comboStep = 0.25f;
        [SerializeField] float comboCap = 3f;

        [Tooltip("Seconds of riding without a trick before the combo lapses.")]
        [SerializeField] float comboGrace = 7f;

        float rotation;             // signed degrees this air; + is nose-up
        float previousAngle;
        float airStart;
        bool airborne;
        float comboExpiresAt;

        public event Action<TrickAward> Banked;
        public event Action<int> Lost;          // points thrown away
        public event Action<int> ComboChanged;

        public int Combo { get; private set; }

        /// <summary>Signed rotations completed in the current air, for the HUD.</summary>
        public float PendingRotations => rotation / 360f;

        public float PendingAirTime => airborne ? Time.time - airStart : 0f;

        public int PendingPoints => airborne ? Estimate(LandingQuality.Clean) : 0;

        void Awake()
        {
            if (bike == null) bike = GetComponentInParent<BikeController>();
        }

        void OnEnable()
        {
            if (bike == null) return;
            bike.Launched += OnLaunched;
            bike.Landed += OnLanded;
            bike.Wiped += OnWiped;
        }

        void OnDisable()
        {
            if (bike == null) return;
            bike.Launched -= OnLaunched;
            bike.Landed -= OnLanded;
            bike.Wiped -= OnWiped;
        }

        void Update()
        {
            if (airborne) Accumulate();
            else if (Combo > 0 && Time.time > comboExpiresAt) SetCombo(0);
        }

        void Accumulate()
        {
            float angle = transform.eulerAngles.z;
            rotation += Mathf.DeltaAngle(previousAngle, angle);
            previousAngle = angle;
        }

        void OnLaunched(float launchSpeed)
        {
            airborne = true;
            rotation = 0f;
            airStart = Time.time;
            previousAngle = transform.eulerAngles.z;
        }

        void OnLanded(LandingQuality quality, float impact)
        {
            if (!airborne) return;
            Accumulate();
            airborne = false;

            if (quality == LandingQuality.Wipeout)
            {
                int lost = Estimate(LandingQuality.Clean);
                if (lost > 0) Lost?.Invoke(lost);
                Reset();
                return;
            }

            int points = Estimate(quality);
            if (points <= 0)
            {
                Reset();
                return;
            }

            SetCombo(Combo + 1);
            comboExpiresAt = Time.time + comboGrace;
            Banked?.Invoke(new TrickAward(BuildLabel(quality), points, Combo, quality,
                                          FlipCount));
            Reset();
        }

        void OnWiped()
        {
            if (airborne)
            {
                int lost = Estimate(LandingQuality.Clean);
                if (lost > 0) Lost?.Invoke(lost);
            }
            airborne = false;
            Reset();
            SetCombo(0);
        }

        void Reset()
        {
            rotation = 0f;
        }

        void SetCombo(int value)
        {
            value = Mathf.Max(0, value);
            if (value == Combo) return;
            Combo = value;
            ComboChanged?.Invoke(Combo);
        }

        // ------------------------------------------------------------ scoring --
        int FlipCount => Mathf.FloorToInt(Mathf.Abs(rotation) / 330f);

        TrickType Direction =>
            FlipCount == 0 ? TrickType.None :
            rotation > 0f ? TrickType.BackFlip : TrickType.FrontFlip;

        float AirTimeUsed => Mathf.Max(0f, Time.time - airStart);

        int Estimate(LandingQuality quality)
        {
            int flips = FlipCount;
            float air = AirTimeUsed;
            if (flips == 0 && air < minPaidAir) return 0;

            int raw = 0;
            for (int i = 1; i <= flips; i++) raw += flipBase * i;

            if (air > minPaidAir)
            {
                int steps = Mathf.FloorToInt((air - minPaidAir) / 0.5f);
                raw += Mathf.Min(steps * airBonusPerHalfSecond, airBonusCap);
            }

            float multiplier = LandingMultiplier(quality) * ComboMultiplier(Combo + 1);
            return Mathf.RoundToInt(raw * multiplier);
        }

        float LandingMultiplier(LandingQuality quality) => quality switch
        {
            LandingQuality.Perfect => perfectBonus,
            LandingQuality.Clean => cleanBonus,
            _ => 1f,
        };

        float ComboMultiplier(int combo) =>
            Mathf.Min(1f + Mathf.Max(0, combo - 1) * comboStep, comboCap);

        static readonly string[] Counts = { "", "", "DOUBLE ", "TRIPLE ", "QUAD " };

        string BuildLabel(LandingQuality quality)
        {
            var sb = new StringBuilder();
            int flips = FlipCount;

            // Plain and factual. The comic burst carries the noise; this line is
            // the receipt, and two shouts saying the same thing is one too many.
            if (flips > 0)
            {
                sb.Append(flips < Counts.Length ? Counts[flips] : flips + "x ");
                sb.Append(Direction == TrickType.BackFlip ? "BACKFLIP" : "FRONTFLIP");
            }
            else
            {
                sb.Append(AirTimeUsed >= 2.4f ? "BIG AIR" : "AIR");
            }

            if (quality == LandingQuality.Perfect) sb.Append("  PERFECT");
            return sb.ToString();
        }
    }
}
