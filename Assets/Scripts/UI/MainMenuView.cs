using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// Title screen. The track runs behind it as a slowly drifting backdrop, so
    /// the menu sits in the world rather than on a flat colour.
    /// </summary>
    public class MainMenuView : MonoBehaviour
    {
        [SerializeField] string title = "DIRT TRAIL";
        [SerializeField] string subtitle = "ONE TRACK. TWO BIKES. NO EXCUSES.";

        MenuList menu;

        void Start()
        {
            Settings.Apply();
            RideInput.Forget();
            Build();
        }

        void Update() => menu?.Tick();

        void Build()
        {
            var canvas = UIBuild.Screen("MainMenu", 5);
            canvas.transform.SetParent(transform, false);
            var root = canvas.transform;

            var column = UIBuild.Box("Column", root, new Vector2(0f, 1f), new Vector2(0f, 1f),
                                     new Vector2(160f, -180f), Vector2.zero);

            var titleBox = UIBuild.Box("Title", column, new Vector2(0f, 1f), new Vector2(0f, 1f),
                                       Vector2.zero, new Vector2(1000f, 150f));
            UIBuild.Fit(UIBuild.FillLabel("Label", titleBox, title, 132f, UISkin.Sand,
                                          TMPro.TextAlignmentOptions.TopLeft));

            UIBuild.Rule(column, new Vector2(0f, 1f), new Vector2(8f, -168f), 420f);

            var subBox = UIBuild.Box("Sub", column, new Vector2(0f, 1f), new Vector2(0f, 1f),
                                     new Vector2(8f, -190f), new Vector2(900f, 34f));
            UIBuild.Fit(UIBuild.FillLabel("Label", subBox, subtitle, 24f, UISkin.Clay,
                                          TMPro.TextAlignmentOptions.TopLeft));

            menu = new MenuList();
            float y = -300f;
            menu.Add(UIBuild.Row(column, "RIDE", new Vector2(0f, y)), Ride);
            menu.Add(UIBuild.Row(column, "TRACKS", new Vector2(0f, y - 82f)),
                     Routes.GoTrackSelect);
            menu.Add(UIBuild.Row(column, "GARAGE", new Vector2(0f, y - 164f)),
                     Routes.GoGarage);
            menu.Add(UIBuild.Row(column, "QUIT", new Vector2(0f, y - 246f)), Quit);

            // Fitted after the content exists, then pushed to the back.
            UIBuild.PanelBehind(column);

            BuildBests(root);
            BuildHint(root);
        }

        void BuildBests(Transform root)
        {
            // Bottom right, quiet. Names the selected track so RIDE is unambiguous.
            var track = TrackRoster.Selected;
            if (track == null) return;

            var box = UIBuild.Box("Bests", root, new Vector2(1f, 0f), new Vector2(1f, 0f),
                                  new Vector2(-70f, 70f), new Vector2(620f, 90f));

            string line = track.displayName;
            int best = Progress.BestScore(track.key);
            if (best > 0)
            {
                line += "     BEST " + best;
                if (Progress.HasBestTime(track.key))
                    line += "  " + Progress.FormatTime(Progress.BestTime(track.key));
            }

            UIBuild.Fit(UIBuild.FillLabel("Label", box, line, 26f, UISkin.SandDim,
                                          TMPro.TextAlignmentOptions.BottomRight));
        }

        void BuildHint(Transform root)
        {
            var box = UIBuild.Box("Hint", root, new Vector2(0f, 0f), new Vector2(0f, 0f),
                                  new Vector2(70f, 60f), new Vector2(900f, 70f));
            UIBuild.FillLabel("Label", box,
                              "W THROTTLE    S BRAKE    A D LEAN    SHIFT NITRO    R RESTART",
                              22f, UISkin.SandDim, TMPro.TextAlignmentOptions.BottomLeft);
        }

        void Ride()
        {
            // First time through, show the garage so the choice is made deliberately.
            if (!Progress.SeenGarage) Routes.GoGarage();
            else Routes.GoTrack();
        }

        void Quit()
        {
#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }
    }
}
