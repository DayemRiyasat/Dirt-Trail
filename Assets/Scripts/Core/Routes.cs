using UnityEngine.SceneManagement;

namespace DirtTrail
{
    /// <summary>
    /// Scene names in one place. Track scenes are named by their TrackConfig,
    /// so adding a level means adding an asset and a build-settings entry, not
    /// editing this file.
    /// </summary>
    public static class Routes
    {
        public const string MainMenu = "MainMenu";
        public const string Garage = "Garage";
        public const string TrackSelect = "TrackSelect";
        public const string FallbackTrack = "RidgeRun";

        public static void GoMainMenu() => Load(MainMenu);
        public static void GoGarage() => Load(Garage);
        public static void GoTrackSelect() => Load(TrackSelect);

        /// <summary>Loads whichever level is currently selected.</summary>
        public static void GoTrack()
        {
            var track = TrackRoster.Selected;
            Load(track != null && !string.IsNullOrEmpty(track.sceneName)
                 ? track.sceneName : FallbackTrack);
        }

        /// <summary>Reload the active scene. The retry path, so it must be cheap.</summary>
        public static void Restart()
        {
            UnityEngine.Time.timeScale = 1f;
            SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
        }

        static void Load(string scene)
        {
            UnityEngine.Time.timeScale = 1f;
            SceneManager.LoadScene(scene);
        }
    }
}
