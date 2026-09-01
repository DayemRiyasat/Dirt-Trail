using UnityEngine;

namespace DirtTrail
{
    /// <summary>One level: what it is called, what it feels like, where it lives.</summary>
    [CreateAssetMenu(fileName = "Track", menuName = "Dirt Trail/Track")]
    public class TrackConfig : ScriptableObject
    {
        [Tooltip("Stable id used for the saved bests. Never rename this.")]
        public string key = "RidgeRun";

        public string displayName = "RIDGE RUN";

        [TextArea(2, 3)]
        public string blurb = "The one you learn on.";

        [Tooltip("Scene name, which must also be in Build Settings.")]
        public string sceneName = "RidgeRun";

        [Tooltip("Length in world units, for the select screen.")]
        public float length = 1046f;

        [Tooltip("How many takeoffs, for the select screen.")]
        public int jumps = 9;

        public Color tint = new Color(0.85f, 0.37f, 0.15f, 1f);
    }
}
