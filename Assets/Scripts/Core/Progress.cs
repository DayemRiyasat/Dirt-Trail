using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// Everything that survives a scene load: which bike and which track were
    /// picked, and the personal bests. Bests are kept per track, keyed on the
    /// track's stable id rather than its index, so reordering the roster or
    /// adding a level never shuffles anyone's records.
    /// </summary>
    public static class Progress
    {
        const string BikeKey = "dt.bike";
        const string TrackKey = "dt.track";
        const string SeenGarageKey = "dt.seen.garage";

        static string ScoreKey(string track) => "dt.best.score." + track;
        static string TimeKey(string track) => "dt.best.time." + track;

        /// <summary>Index into <see cref="BikeRoster"/>.</summary>
        public static int SelectedBike
        {
            get => Mathf.Clamp(PlayerPrefs.GetInt(BikeKey, 0), 0, 8);
            set { PlayerPrefs.SetInt(BikeKey, value); PlayerPrefs.Save(); }
        }

        /// <summary>Index into <see cref="TrackRoster"/>.</summary>
        public static int SelectedTrack
        {
            get => Mathf.Clamp(PlayerPrefs.GetInt(TrackKey, 0), 0, 16);
            set { PlayerPrefs.SetInt(TrackKey, value); PlayerPrefs.Save(); }
        }

        public static bool SeenGarage
        {
            get => PlayerPrefs.GetInt(SeenGarageKey, 0) == 1;
            set { PlayerPrefs.SetInt(SeenGarageKey, value ? 1 : 0); PlayerPrefs.Save(); }
        }

        // ------------------------------------------------------------ bests --
        public static int BestScore(string track) =>
            string.IsNullOrEmpty(track) ? 0 : PlayerPrefs.GetInt(ScoreKey(track), 0);

        /// <summary>Seconds. Zero means no finish has been recorded yet.</summary>
        public static float BestTime(string track) =>
            string.IsNullOrEmpty(track) ? 0f : PlayerPrefs.GetFloat(TimeKey(track), 0f);

        public static bool HasBestTime(string track) => BestTime(track) > 0.01f;

        /// <summary>Returns true if this run beat the stored score.</summary>
        public static bool SubmitScore(string track, int score)
        {
            if (string.IsNullOrEmpty(track) || score <= BestScore(track)) return false;
            PlayerPrefs.SetInt(ScoreKey(track), score);
            PlayerPrefs.Save();
            return true;
        }

        /// <summary>Returns true if this run beat the stored time. Finishes only.</summary>
        public static bool SubmitTime(string track, float seconds)
        {
            if (string.IsNullOrEmpty(track) || seconds <= 0f) return false;
            if (HasBestTime(track) && seconds >= BestTime(track)) return false;
            PlayerPrefs.SetFloat(TimeKey(track), seconds);
            PlayerPrefs.Save();
            return true;
        }

        public static void Wipe(string track)
        {
            if (string.IsNullOrEmpty(track)) return;
            PlayerPrefs.DeleteKey(ScoreKey(track));
            PlayerPrefs.DeleteKey(TimeKey(track));
            PlayerPrefs.Save();
        }

        public static string FormatTime(float seconds)
        {
            if (seconds <= 0f) return "--:--";
            int m = Mathf.FloorToInt(seconds / 60f);
            float s = seconds - m * 60f;
            return string.Format("{0}:{1:00.00}", m, s);
        }
    }
}
