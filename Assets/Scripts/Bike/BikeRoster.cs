using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// The two bikes, in one asset loaded from Resources so the garage and the
    /// track agree on the selection without passing references between scenes.
    /// </summary>
    [CreateAssetMenu(fileName = "BikeRoster", menuName = "Dirt Trail/Bike Roster")]
    public class BikeRoster : ScriptableObject
    {
        public const string ResourcePath = "BikeRoster";

        [SerializeField] BikeConfig[] bikes;

        static BikeRoster cached;

        public static BikeRoster Load()
        {
            if (cached == null) cached = Resources.Load<BikeRoster>(ResourcePath);
            return cached;
        }

        public int Count => bikes == null ? 0 : bikes.Length;

        public BikeConfig this[int index]
        {
            get
            {
                if (bikes == null || bikes.Length == 0) return null;
                return bikes[((index % bikes.Length) + bikes.Length) % bikes.Length];
            }
        }

        /// <summary>The bike chosen in the garage, or the first one as a fallback.</summary>
        public static BikeConfig Selected
        {
            get
            {
                var roster = Load();
                return roster == null ? null : roster[Progress.SelectedBike];
            }
        }
    }
}
