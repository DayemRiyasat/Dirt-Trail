using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace DirtTrail
{
    /// <summary>
    /// Bike select. Two bikes, so the whole screen is one parked bike, three
    /// stat rows and a line of text - no carousel, no cards, no shop.
    /// Left and right change the bike; the menu below is just RIDE and BACK.
    /// </summary>
    public class GarageView : MonoBehaviour
    {
        [SerializeField] BikeDisplay display;

        [Tooltip("Ticks per stat row. Ten reads as a rating without looking like a bar chart.")]
        [SerializeField] int ticksPerStat = 10;

        MenuList menu;
        BikeRoster roster;
        int index;

        TextMeshProUGUI nameLabel, blurbLabel, counter;
        UnityEngine.UI.Image panel;
        readonly List<Image[]> statRows = new();

        static readonly string[] StatNames = { "SPEED", "GRIP", "AIR" };

        void Start()
        {
            Settings.Apply();
            RideInput.Forget();

            roster = BikeRoster.Load();
            index = Progress.SelectedBike;
            Progress.SeenGarage = true;

            Build();
            Refresh();
        }

        void Update()
        {
            menu?.Tick();

            float lean = RideInput.Lean;
            if (Mathf.Abs(lean) > 0.6f) Nudge(lean > 0f ? 1 : -1);
        }

        float nextNudge;

        void Nudge(int direction)
        {
            if (Time.unscaledTime < nextNudge) return;
            nextNudge = Time.unscaledTime + 0.3f;
            Select(index + direction);
        }

        void Build()
        {
            var canvas = UIBuild.Screen("Garage", 5);
            canvas.transform.SetParent(transform, false);
            var root = canvas.transform;

            var column = UIBuild.Box("Column", root, new Vector2(0f, 1f), new Vector2(0f, 1f),
                                     new Vector2(150f, -150f), Vector2.zero);

            var head = UIBuild.Box("Heading", column, new Vector2(0f, 1f), new Vector2(0f, 1f),
                                   Vector2.zero, new Vector2(800f, 100f));
            UIBuild.FillLabel("Label", head, "GARAGE", 88f, UISkin.Sand,
                              TextAlignmentOptions.TopLeft);
            UIBuild.Rule(column, new Vector2(0f, 1f), new Vector2(6f, -112f), 260f);

            var nameBox = UIBuild.Box("Name", column, new Vector2(0f, 1f), new Vector2(0f, 1f),
                                      new Vector2(4f, -150f), new Vector2(800f, 90f));
            nameLabel = UIBuild.FillLabel("Label", nameBox, "", 72f, UISkin.Orange,
                                          TextAlignmentOptions.TopLeft);

            var blurbBox = UIBuild.Box("Blurb", column, new Vector2(0f, 1f), new Vector2(0f, 1f),
                                       new Vector2(6f, -240f), new Vector2(660f, 66f));
            blurbLabel = UIBuild.FillLabel("Label", blurbBox, "", 28f, UISkin.Clay,
                                           TextAlignmentOptions.TopLeft);
            // Bike blurbs are authored data and vary in length; let them wrap.
            blurbLabel.textWrappingMode = TextWrappingModes.Normal;

            BuildStats(column, new Vector2(6f, -320f));

            var counterBox = UIBuild.Box("Counter", root, new Vector2(1f, 1f),
                                         new Vector2(1f, 1f), new Vector2(-70f, -60f),
                                         new Vector2(300f, 40f));
            counter = UIBuild.FillLabel("Label", counterBox, "", 26f, UISkin.SandDim,
                                        TextAlignmentOptions.TopRight);

            var hintBox = UIBuild.Box("Hint", root, new Vector2(0f, 0f), new Vector2(0f, 0f),
                                      new Vector2(70f, 60f), new Vector2(900f, 40f));
            UIBuild.FillLabel("Label", hintBox, "A D  SWITCH BIKE", 22f, UISkin.SandDim,
                              TextAlignmentOptions.BottomLeft);

            menu = new MenuList();
            menu.Add(UIBuild.Row(column, "RIDE", new Vector2(0f, -560f)), Ride);
            menu.Add(UIBuild.Row(column, "BACK", new Vector2(0f, -636f)), Routes.GoMainMenu);
            menu.Cancelled += Routes.GoMainMenu;

            panel = UIBuild.PanelBehind(column);
            fitColumn = column;
        }

        RectTransform fitColumn;

        void BuildStats(RectTransform column, Vector2 origin)
        {
            var skin = UISkin.Load();
            for (int row = 0; row < StatNames.Length; row++)
            {
                float y = origin.y - row * 56f;

                var capBox = UIBuild.Box("Cap", column, new Vector2(0f, 1f), new Vector2(0f, 1f),
                                         new Vector2(origin.x, y), new Vector2(180f, 34f));
                UIBuild.FillLabel("Label", capBox, StatNames[row], 24f, UISkin.SandDim,
                                  TextAlignmentOptions.Left);

                var ticks = new Image[ticksPerStat];
                for (int i = 0; i < ticksPerStat; i++)
                {
                    var tick = UIBuild.Box("Tick", column, new Vector2(0f, 1f),
                                           new Vector2(0f, 1f),
                                           new Vector2(origin.x + 200f + i * 30f, y - 4f),
                                           new Vector2(18f, 26f));
                    var img = tick.gameObject.AddComponent<Image>();
                    img.sprite = skin != null ? skin.plateSand : null;
                    img.type = Image.Type.Sliced;
                    img.color = UISkin.Bark;
                    img.raycastTarget = false;
                    ticks[i] = img;
                }
                statRows.Add(ticks);
            }
        }

        void Select(int next)
        {
            if (roster == null || roster.Count == 0) return;
            index = ((next % roster.Count) + roster.Count) % roster.Count;
            Progress.SelectedBike = index;
            Refresh();
        }

        void Refresh()
        {
            if (roster == null || roster.Count == 0) return;
            var config = roster[index];
            if (config == null) return;

            nameLabel.text = config.displayName;
            blurbLabel.text = config.blurb;
            counter.text = (index + 1) + " / " + roster.Count;

            SetTicks(0, config.statSpeed);
            SetTicks(1, config.statGrip);
            SetTicks(2, config.statAir);

            // Names and blurbs vary per bike, so the boxes and the plate behind
            // them are re-measured every time the selection changes.
            UIBuild.Fit(nameLabel);
            UIBuild.Fit(blurbLabel);
            UIBuild.Fit(counter);
            UIBuild.RefitPanel(panel, fitColumn);

            if (display != null) display.Apply(config);
        }

        void SetTicks(int row, float value01)
        {
            if (row >= statRows.Count) return;
            int lit = Mathf.RoundToInt(Mathf.Clamp01(value01) * ticksPerStat);
            var ticks = statRows[row];
            for (int i = 0; i < ticks.Length; i++)
                ticks[i].color = i < lit ? UISkin.Orange : UISkin.Bark;
        }

        void Ride()
        {
            Progress.SelectedBike = index;
            Routes.GoTrack();
        }
    }
}
