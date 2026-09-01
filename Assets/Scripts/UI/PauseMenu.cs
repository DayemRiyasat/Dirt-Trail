using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// Esc or Start. Also carries the two settings worth having on a track this
    /// size: sound on or off, and shake on or off.
    /// </summary>
    public class PauseMenu : OverlayScreen
    {
        [SerializeField] RunManager run;

        MenuItem soundRow, shakeRow;

        protected override string Heading => "PAUSED";

        void Awake()
        {
            if (run == null) run = FindFirstObjectByType<RunManager>();
        }

        protected override void PopulateBody(RectTransform column)
        {
            Stat(column, "TRACK", run != null ? run.TrackName : "TRACK",
             new Vector2(6f, -150f), 44f);
        }

        protected override void PopulateMenu(MenuList menu, RectTransform column)
        {
            float y = -280f;
            menu.Add(UIBuild.Row(column, "RESUME", new Vector2(0f, y)), Resume);
            menu.Add(UIBuild.Row(column, "RETRY", new Vector2(0f, y - 76f)), Routes.Restart);

            soundRow = UIBuild.Row(column, SoundLabel(), new Vector2(0f, y - 152f));
            menu.Add(soundRow, ToggleSound);

            shakeRow = UIBuild.Row(column, ShakeLabel(), new Vector2(0f, y - 228f));
            menu.Add(shakeRow, ToggleShake);

            menu.Add(UIBuild.Row(column, "GARAGE", new Vector2(0f, y - 304f)), Routes.GoGarage);
            menu.Add(UIBuild.Row(column, "QUIT TO MENU", new Vector2(0f, y - 380f)),
                     Routes.GoMainMenu);

            menu.Cancelled += Resume;
        }

        protected override void Update()
        {
            base.Update();

            if (run == null) return;
            if (run.Phase == RunPhase.Finished) return;

            if (RideInput.PausePressed)
            {
                if (Visible) Resume();
                else Open();
            }
        }

        void Open()
        {
            run.SetPaused(true);
            Show();
        }

        void Resume()
        {
            Hide();
            run.SetPaused(false);
        }

        // ------------------------------------------------------------ options --
        static string SoundLabel() => "SOUND   " + (Settings.SoundOn ? "ON" : "OFF");
        static string ShakeLabel() => "SHAKE   " + (Settings.ShakeOn ? "ON" : "OFF");

        void ToggleSound()
        {
            Settings.SoundOn = !Settings.SoundOn;
            if (soundRow != null) soundRow.Label.text = SoundLabel();
        }

        void ToggleShake()
        {
            Settings.ShakeOn = !Settings.ShakeOn;
            if (shakeRow != null) shakeRow.Label.text = ShakeLabel();
        }
    }
}
