using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace DirtTrail
{
    /// <summary>
    /// The riding HUD: four corner readouts and a progress rule, and nothing
    /// else. Every event - a landed flip, a pickup, a wipeout - is announced by
    /// a comic burst in the world instead, so there is no running caption
    /// repeating in words what the burst already said in pictures.
    /// </summary>
    public class HudView : MonoBehaviour
    {
        [SerializeField] RunManager run;

        TextMeshProUGUI scoreValue, bestValue, comboTag, pendingTag;
        TextMeshProUGUI timeValue, wipeTag;
        Image progressFill;
        readonly List<Image> nitroPips = new();

        int shownScore;

        void Awake()
        {
            if (run == null) run = FindFirstObjectByType<RunManager>();
            Build();
        }

        // ------------------------------------------------------------- build --
        void Build()
        {
            var canvas = UIBuild.Screen("HUD", 10);
            canvas.transform.SetParent(transform, false);
            var root = canvas.transform;

            // progress rule, hairline along the very top
            var track = UIBuild.Rect("Progress", root, new Vector2(0f, 1f), new Vector2(1f, 1f),
                                     new Vector2(0f, -7f), new Vector2(0f, 0f));
            UIBuild.Fill(track, new Color(UISkin.Bark.r, UISkin.Bark.g, UISkin.Bark.b, 0.55f));
            var fill = UIBuild.Rect("Fill", track, Vector2.zero, new Vector2(0f, 1f),
                                    Vector2.zero, Vector2.zero);
            fill.anchorMax = new Vector2(0f, 1f);
            progressFill = UIBuild.Fill(fill, UISkin.Orange);
            progressFill.rectTransform.sizeDelta = new Vector2(0f, 0f);

            // --- top left: score --------------------------------------------
            var tl = new Vector2(0f, 1f);
            Anchor(root, "SCORE", 24f, UISkin.SandDim, tl, new Vector2(46f, -34f),
                   new Vector2(260f, 30f), TextAlignmentOptions.TopLeft);

            scoreValue = Anchor(root, "0", 76f, UISkin.Sand, tl, new Vector2(44f, -60f),
                                new Vector2(420f, 84f), TextAlignmentOptions.TopLeft);

            comboTag = Anchor(root, "", 40f, UISkin.Orange, tl, new Vector2(46f, -150f),
                              new Vector2(200f, 46f), TextAlignmentOptions.TopLeft);

            pendingTag = Anchor(root, "", 28f, new Color(1f, 1f, 1f, 0.45f), tl,
                                new Vector2(200f, -150f), new Vector2(260f, 40f),
                                TextAlignmentOptions.TopLeft);

            bestValue = Anchor(root, "", 22f, UISkin.SandDim, tl, new Vector2(46f, -196f),
                               new Vector2(320f, 30f), TextAlignmentOptions.TopLeft);

            // --- top right: clock -------------------------------------------
            var tr = new Vector2(1f, 1f);
            Anchor(root, "TIME", 24f, UISkin.SandDim, tr, new Vector2(-46f, -34f),
                   new Vector2(260f, 30f), TextAlignmentOptions.TopRight, new Vector2(1f, 1f));
            timeValue = Anchor(root, "0:00.00", 54f, UISkin.Sand, tr, new Vector2(-44f, -60f),
                               new Vector2(380f, 66f), TextAlignmentOptions.TopRight,
                               new Vector2(1f, 1f));
            wipeTag = Anchor(root, "", 22f, UISkin.SandDim, tr, new Vector2(-46f, -132f),
                             new Vector2(320f, 30f), TextAlignmentOptions.TopRight,
                             new Vector2(1f, 1f));

            // --- bottom left: nitro ------------------------------------------
            var bl = new Vector2(0f, 0f);
            Anchor(root, "NITRO", 22f, UISkin.SandDim, bl, new Vector2(46f, 78f),
                   new Vector2(200f, 28f), TextAlignmentOptions.BottomLeft,
                   new Vector2(0f, 0f));

            var skin = UISkin.Load();
            for (int i = 0; i < 3; i++)
            {
                var pip = UIBuild.Box("Pip" + i, root, bl, new Vector2(0f, 0f),
                                      new Vector2(46f + i * 40f, 36f), new Vector2(30f, 30f));
                var img = pip.gameObject.AddComponent<Image>();
                img.sprite = skin != null ? skin.chevron : null;
                img.color = UISkin.Bark;
                img.raycastTarget = false;
                nitroPips.Add(img);
            }
        }

        TextMeshProUGUI Anchor(Transform root, string text, float size, Color color,
                               Vector2 anchor, Vector2 position, Vector2 boxSize,
                               TextAlignmentOptions align, Vector2? pivot = null)
        {
            var box = UIBuild.Box("T " + text, root, anchor, pivot ?? new Vector2(0f, 1f),
                                  position, boxSize);
            return UIBuild.FillLabel("Label", box, text, size, color, align);
        }

        // ------------------------------------------------------------ update --
        void Start()
        {
            string key = run != null ? run.TrackKey : null;
            int best = Progress.BestScore(key);
            bestValue.text = best > 0 ? "BEST " + best : "";
        }

        void Update()
        {
            if (run == null) return;

            // Score counts up rather than snapping, so a big trick reads as a big trick.
            shownScore = Mathf.RoundToInt(
                Mathf.MoveTowards(shownScore, run.Score,
                                  Mathf.Max(240f, Mathf.Abs(run.Score - shownScore) * 6f)
                                  * Time.unscaledDeltaTime));
            scoreValue.text = shownScore.ToString();

            timeValue.text = Progress.FormatTime(run.Elapsed);
            wipeTag.text = run.Wipeouts > 0
                ? (run.Wipeouts == 1 ? "1 WIPEOUT" : run.Wipeouts + " WIPEOUTS")
                : "";

            var tricks = run.Tricks;
            int combo = tricks != null ? tricks.Combo : 0;
            comboTag.text = combo >= 2 ? "x" + combo : "";

            int pending = tricks != null ? tricks.PendingPoints : 0;
            pendingTag.text = pending > 0 ? "+" + pending : "";

            UpdateNitro();
            UpdateProgress();
        }

        void UpdateNitro()
        {
            var bike = run.Bike;
            int charges = bike != null ? bike.NitroCharges : 0;
            bool burning = bike != null && bike.NitroActive;

            for (int i = 0; i < nitroPips.Count; i++)
            {
                bool lit = i < charges;
                var target = burning && i == 0 ? UISkin.Sand
                           : lit ? UISkin.Orange
                           : UISkin.Bark;
                nitroPips[i].color = Color.Lerp(nitroPips[i].color, target,
                                                Time.unscaledDeltaTime * 12f);
            }
        }

        void UpdateProgress()
        {
            if (progressFill == null) return;
            var rt = progressFill.rectTransform;
            rt.anchorMax = new Vector2(Mathf.Clamp01(run.TrackProgress), 1f);
            rt.offsetMax = new Vector2(0f, 0f);
            rt.offsetMin = new Vector2(0f, 0f);
        }
    }
}
