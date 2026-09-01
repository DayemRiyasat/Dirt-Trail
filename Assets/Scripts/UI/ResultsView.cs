using TMPro;
using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// Shown when the run ends. Kept as an overlay rather than a fourth scene so
    /// RETRY is instant - the track is already loaded and warm behind it.
    /// </summary>
    public class ResultsView : OverlayScreen
    {
        [SerializeField] RunManager run;

        TextMeshProUGUI timeValue, scoreValue, wipeValue, bestLine;
        RectTransform tagRow;
        bool shown;

        protected override string Heading => run != null && run.Outcome == RunOutcome.Finished
            ? "TRACK DONE"
            : "RETIRED";

        void Awake()
        {
            if (run == null) run = FindFirstObjectByType<RunManager>();
        }

        void OnEnable()
        {
            if (run != null) run.PhaseChanged += OnPhase;
        }

        void OnDisable()
        {
            if (run != null) run.PhaseChanged -= OnPhase;
        }

        void OnPhase(RunPhase phase)
        {
            if (phase != RunPhase.Finished || shown) return;
            shown = true;
            Show();
            Populate();
        }

        protected override void PopulateBody(RectTransform column)
        {
            timeValue = Stat(column, "TIME", "--:--", new Vector2(6f, -160f), 64f);
            scoreValue = Stat(column, "SCORE", "0", new Vector2(6f, -262f), 64f);
            wipeValue = Stat(column, "WIPEOUTS", "0", new Vector2(6f, -364f), 44f);

            var bestBox = UIBuild.Box("Best", column, new Vector2(0f, 1f), new Vector2(0f, 1f),
                                      new Vector2(6f, -440f), new Vector2(700f, 30f));
            bestLine = UIBuild.FillLabel("Label", bestBox, "", 24f, UISkin.SandDim,
                                         TextAlignmentOptions.TopLeft);

            tagRow = UIBuild.Box("Tags", column, new Vector2(0f, 1f), new Vector2(0f, 1f),
                                 new Vector2(500f, -160f), new Vector2(300f, 200f));
        }

        protected override void PopulateMenu(MenuList menu, RectTransform column)
        {
            float y = -510f;
            menu.Add(UIBuild.Row(column, "RETRY", new Vector2(0f, y)), Routes.Restart);
            menu.Add(UIBuild.Row(column, "GARAGE", new Vector2(0f, y - 76f)), Routes.GoGarage);
            menu.Add(UIBuild.Row(column, "MAIN MENU", new Vector2(0f, y - 152f)),
                     Routes.GoMainMenu);
        }

        void Populate()
        {
            if (run == null) return;

            timeValue.text = Progress.FormatTime(run.Elapsed);
            scoreValue.text = run.Score.ToString();
            wipeValue.text = run.Wipeouts.ToString();

            string key = run.TrackKey;
            string best = "BEST " + Progress.BestScore(key);
            if (Progress.HasBestTime(key))
                best += "    " + Progress.FormatTime(Progress.BestTime(key));
            bestLine.text = best;

            float y = 0f;
            if (run.NewBestScore)
            {
                Tag(tagRow, "NEW BEST SCORE", new Vector2(0f, y));
                y -= 54f;
            }
            if (run.NewBestTime) Tag(tagRow, "NEW BEST TIME", new Vector2(0f, y));
        }
    }
}
