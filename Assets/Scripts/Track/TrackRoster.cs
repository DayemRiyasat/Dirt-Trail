using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// The levels, in the order they are meant to be met. Loaded from Resources
    /// so the menu and the track scenes agree on which one is selected without
    /// passing references between scenes.
    /// </summary>
    [CreateAssetMenu(fileName = "TrackRoster", menuName = "Dirt Trail/Track Roster")]
    public class TrackRoster : ScriptableObject
    {
        public const string ResourcePath = "TrackRoster";

        [SerializeField] TrackConfig[] tracks;

        static TrackRoster cached;

        public static TrackRoster Load()
        {
            if (cached == null) cached = Resources.Load<TrackRoster>(ResourcePath);
            return cached;
        }

        public int Count => tracks == null ? 0 : tracks.Length;

        public TrackConfig this[int index]
        {
            get
            {
                if (tracks == null || tracks.Length == 0) return null;
                return tracks[((index % tracks.Length) + tracks.Length) % tracks.Length];
            }
        }

        public static TrackConfig Selected
        {
            get
            {
                var roster = Load();
                return roster == null ? null : roster[Progress.SelectedTrack];
            }
        }

        public TrackConfig Find(string key)
        {
            if (tracks == null) return null;
            foreach (var t in tracks)
                if (t != null && t.key == key) return t;
            return null;
        }
    }
}
