using System.Collections.Generic;
using TMPro;
using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// Pick a level. Three of them, so it is a list rather than a carousel:
    /// name, one line on what it is like, and your record on it. Highlighting a
    /// row previews it, which is the only thing that makes a list of names into
    /// a choice you can actually make.
    /// </summary>
    public class TrackSelectView : MonoBehaviour
    {
        MenuList menu;
        TrackRoster roster;
        int index;

        TextMeshProUGUI blurbLabel, statsLabel, bestLabel;
        UnityEngine.UI.Image panel;
        RectTransform column;
        readonly List<MenuItem> rows = new();

        void Start()
        {
            Settings.Apply();
            RideInput.Forget();

            roster = TrackRoster.Load();
            index = Progress.SelectedTrack;
            Build();
            Preview(index);
        }

        void Update() => menu?.Tick();

        void Build()
        {
            var canvas = UIBuild.Screen("TrackSelect", 5);
            canvas.transform.SetParent(transform, false);
            var root = canvas.transform;

            column = UIBuild.Box("Column", root, new Vector2(0f, 1f), new Vector2(0f, 1f),
                                     new Vector2(150f, -150f), Vector2.zero);

            var head = UIBuild.Box("Heading", column, new Vector2(0f, 1f), new Vector2(0f, 1f),
                                   Vector2.zero, new Vector2(760f, 100f));
            UIBuild.FillLabel("Label", head, "TRACKS", 88f, UISkin.Sand,
                              TextAlignmentOptions.TopLeft);
            UIBuild.Rule(column, new Vector2(0f, 1f), new Vector2(6f, -112f), 250f);

            menu = new MenuList();
            menu.SelectionChanged += OnRowChanged;
            menu.Cancelled += Routes.GoMainMenu;

            float y = -160f;
            int count = roster != null ? roster.Count : 0;
            for (int i = 0; i < count; i++)
            {
                var track = roster[i];
                var row = UIBuild.Row(column, track != null ? track.displayName : "TRACK",
                                      new Vector2(0f, y));
                rows.Add(row);
                int captured = i;
                menu.Add(row, () => Ride(captured));
                y -= 78f;
            }

            // Detail for whichever row is highlighted, below the list.
            float detail = y - 24f;
            blurbLabel = Line(column, new Vector2(6f, detail), 28f, UISkin.Clay, 700f);
            statsLabel = Line(column, new Vector2(6f, detail - 44f), 24f, UISkin.SandDim, 700f);
            bestLabel = Line(column, new Vector2(6f, detail - 78f), 24f, UISkin.Orange, 700f);

            menu.Add(UIBuild.Row(column, "BACK", new Vector2(0f, detail - 140f)),
                     Routes.GoMainMenu);

            var hint = UIBuild.Box("Hint", root, new Vector2(0f, 0f), new Vector2(0f, 0f),
                                   new Vector2(70f, 60f), new Vector2(900f, 40f));
            UIBuild.FillLabel("Label", hint, "CLICK A TRACK, OR ARROWS AND ENTER", 22f,
                              UISkin.SandDim, TextAlignmentOptions.BottomLeft);

            panel = UIBuild.PanelBehind(column);
            menu.Select(Mathf.Clamp(index, 0, Mathf.Max(0, count - 1)));
        }

        static TextMeshProUGUI Line(RectTransform column, Vector2 at, float size,
                                    Color color, float width)
        {
            var box = UIBuild.Box("Line", column, new Vector2(0f, 1f), new Vector2(0f, 1f),
                                  at, new Vector2(width, size + 12f));
            return UIBuild.FillLabel("Label", box, "", size, color,
                                     TextAlignmentOptions.TopLeft);
        }

        void OnRowChanged(int row)
        {
            // The last row is BACK, which has nothing to preview.
            if (roster == null || row >= roster.Count) return;
            Preview(row);
        }

        void Preview(int i)
        {
            if (roster == null || roster.Count == 0) return;
            var track = roster[i];
            if (track == null) return;

            index = i;
            blurbLabel.text = track.blurb;
            statsLabel.text = string.Format("{0:0} UNITS    {1} JUMPS",
                                            track.length, track.jumps);

            int best = Progress.BestScore(track.key);
            bestLabel.text = best > 0
                ? "BEST " + best + (Progress.HasBestTime(track.key)
                    ? "    " + Progress.FormatTime(Progress.BestTime(track.key)) : "")
                : "NOT RIDDEN YET";

            UIBuild.Fit(blurbLabel);
            UIBuild.Fit(statsLabel);
            UIBuild.Fit(bestLabel);
            UIBuild.RefitPanel(panel, column);
        }

        void Ride(int i)
        {
            Progress.SelectedTrack = i;
            Routes.GoTrack();
        }
    }
}
