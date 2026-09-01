using System;
using System.Collections;
using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// Owns one attempt at the track: the clock, the score, where you restart
    /// from, and which of Ready / Riding / Paused / Wiped / Finished you are in.
    /// Everything else in the scene reports to this and reads back from it, so
    /// there is exactly one place that decides what a run is worth.
    /// </summary>
    public class RunManager : MonoBehaviour
    {
        public static RunManager Instance { get; private set; }

        [SerializeField] BikeController bike;
        [SerializeField] TrickSystem tricks;
        [SerializeField] Transform startMarker;
        [SerializeField] Transform finishMarker;

        [Tooltip("Stable id of this level. Bests are stored against it.")]
        [SerializeField] string trackKey = "RidgeRun";

        [SerializeField] string trackName = "RIDGE RUN";

        [Header("Wipeouts")]
        [Tooltip("How long the crash is allowed to play out before you are put back.")]
        [SerializeField] float respawnDelay = 1.15f;

        [Tooltip("Below this world height you are off the map and it counts as a wipeout.")]
        [SerializeField] float killHeight = -400f;

        [Header("Finish")]
        [SerializeField] int finishBonus = 500;

        public RunPhase Phase { get; private set; } = RunPhase.Ready;
        public int Score { get; private set; }
        public int Wipeouts { get; private set; }
        public float Elapsed { get; private set; }
        public RunOutcome Outcome { get; private set; } = RunOutcome.None;

        public bool NewBestScore { get; private set; }
        public bool NewBestTime { get; private set; }

        public string TrackKey => trackKey;
        public string TrackName => trackName;

        public BikeController Bike => bike;
        public TrickSystem Tricks => tricks;

        /// <summary>0..1 along the track, for the HUD progress rule. Not named
        /// Progress: that is the save-data class, and the two collide here.</summary>
        public float TrackProgress
        {
            get
            {
                if (bike == null || startMarker == null || finishMarker == null) return 0f;
                float span = finishMarker.position.x - startMarker.position.x;
                if (Mathf.Abs(span) < 0.01f) return 0f;
                return Mathf.Clamp01((bike.transform.position.x - startMarker.position.x) / span);
            }
        }

        public event Action<int, int> ScoreChanged;        // total, delta
        public event Action<TrickAward> TrickBanked;
        public event Action<int> TrickLost;
        public event Action<PickupConfig> PickupTaken;
        public event Action<RunPhase> PhaseChanged;
        public event Action Wiped;

        Vector2 respawnPoint;
        float respawnRotation;
        Coroutine respawnRoutine;

        void Awake()
        {
            Instance = this;
            RideInput.Forget();
            if (bike == null) bike = FindFirstObjectByType<BikeController>();
            if (tricks == null && bike != null) tricks = bike.GetComponentInChildren<TrickSystem>();
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        void OnEnable()
        {
            if (tricks != null)
            {
                tricks.Banked += OnTrickBanked;
                tricks.Lost += OnTrickLost;
            }
            if (bike != null) bike.Wiped += OnBikeWiped;
            Pickup.Collected += OnPickup;
        }

        void OnDisable()
        {
            if (tricks != null)
            {
                tricks.Banked -= OnTrickBanked;
                tricks.Lost -= OnTrickLost;
            }
            if (bike != null) bike.Wiped -= OnBikeWiped;
            Pickup.Collected -= OnPickup;
        }

        void Start()
        {
            if (bike != null)
            {
                respawnPoint = bike.transform.position;
                respawnRotation = bike.transform.eulerAngles.z;
            }
            SetPhase(RunPhase.Riding);
        }

        void Update()
        {
            if (Phase == RunPhase.Riding)
            {
                Elapsed += Time.deltaTime;
                if (bike != null && bike.transform.position.y < killHeight) bike.Wipeout();
            }

            if (RideInput.RetryPressed && Phase != RunPhase.Ready) Routes.Restart();
        }

        // ------------------------------------------------------------ scoring --
        public void AddScore(int points)
        {
            if (points == 0) return;
            Score = Mathf.Max(0, Score + points);
            ScoreChanged?.Invoke(Score, points);
        }

        void OnTrickBanked(TrickAward award)
        {
            AddScore(award.Points);
            TrickBanked?.Invoke(award);
        }

        void OnTrickLost(int points) => TrickLost?.Invoke(points);

        void OnPickup(PickupConfig config, Vector3 where)
        {
            AddScore(config.bonus);
            PickupTaken?.Invoke(config);
        }

        // ----------------------------------------------------------- wipeouts --
        void OnBikeWiped()
        {
            if (Phase != RunPhase.Riding) return;
            Wipeouts++;
            SetPhase(RunPhase.Wiped);
            Wiped?.Invoke();
            respawnRoutine = StartCoroutine(RespawnAfterDelay());
        }

        IEnumerator RespawnAfterDelay()
        {
            yield return new WaitForSeconds(respawnDelay);
            if (Phase != RunPhase.Wiped) yield break;

            bike.Respawn(respawnPoint, respawnRotation);
            SetPhase(RunPhase.Riding);
            respawnRoutine = null;
        }

        /// <summary>Called by checkpoints as the rider passes them.</summary>
        public void SetRespawn(Vector2 position, float zRotation)
        {
            respawnPoint = position;
            respawnRotation = zRotation;
        }

        // -------------------------------------------------------------- ending --
        public void Finish()
        {
            if (Phase == RunPhase.Finished) return;
            if (respawnRoutine != null) StopCoroutine(respawnRoutine);

            AddScore(finishBonus);
            Outcome = RunOutcome.Finished;
            NewBestScore = Progress.SubmitScore(trackKey, Score);
            NewBestTime = Progress.SubmitTime(trackKey, Elapsed);

            if (bike != null) bike.SetControlsEnabled(false);
            SetPhase(RunPhase.Finished);
        }

        /// <summary>Give up from the pause menu. Scores still count.</summary>
        public void Retire()
        {
            if (Phase == RunPhase.Finished) return;
            Outcome = RunOutcome.Retired;
            NewBestScore = Progress.SubmitScore(trackKey, Score);
            NewBestTime = false;
            if (bike != null) bike.SetControlsEnabled(false);
            SetPhase(RunPhase.Finished);
        }

        // --------------------------------------------------------------- pause --
        public void SetPaused(bool paused)
        {
            if (Phase == RunPhase.Finished) return;
            if (paused && Phase == RunPhase.Paused) return;
            if (!paused && Phase != RunPhase.Paused) return;

            if (paused)
            {
                Time.timeScale = 0f;
                SetPhase(RunPhase.Paused);
            }
            else
            {
                Time.timeScale = 1f;
                SetPhase(bike != null && bike.IsWiped ? RunPhase.Wiped : RunPhase.Riding);
            }
        }

        void SetPhase(RunPhase phase)
        {
            if (Phase == phase) return;
            Phase = phase;
            PhaseChanged?.Invoke(phase);
        }
    }
}
