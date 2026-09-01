using UnityEngine;

namespace DirtTrail
{
    /// <summary>Two options, both worth having. Applied the moment they change.</summary>
    public static class Settings
    {
        const string SoundKey = "dt.sound";
        const string ShakeKey = "dt.shake";

        public static bool SoundOn
        {
            get => PlayerPrefs.GetInt(SoundKey, 1) == 1;
            set
            {
                PlayerPrefs.SetInt(SoundKey, value ? 1 : 0);
                PlayerPrefs.Save();
                Apply();
            }
        }

        public static bool ShakeOn
        {
            get => PlayerPrefs.GetInt(ShakeKey, 1) == 1;
            set
            {
                PlayerPrefs.SetInt(ShakeKey, value ? 1 : 0);
                PlayerPrefs.Save();
            }
        }

        /// <summary>Call once per scene load; AudioListener volume is not persistent.</summary>
        public static void Apply()
        {
            AudioListener.volume = SoundOn ? 1f : 0f;
        }
    }
}
