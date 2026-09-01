using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace DirtTrail
{
    /// <summary>
    /// Shared plumbing for the two overlays that sit on top of the track: build
    /// once on first show, then just toggle. Both dim the game behind a flat
    /// scrim - no blur, no frosted panel.
    /// </summary>
    public abstract class OverlayScreen : MonoBehaviour
    {
        protected MenuList Menu { get; private set; }
        protected RectTransform Column { get; private set; }

        Canvas canvas;
        bool built;

        public bool Visible => canvas != null && canvas.gameObject.activeSelf;

        protected abstract string Heading { get; }
        protected virtual int SortOrder => 20;
        protected virtual float ScrimAlpha => 0.82f;

        protected virtual void PopulateBody(RectTransform column) { }
        protected abstract void PopulateMenu(MenuList menu, RectTransform column);

        protected void EnsureBuilt()
        {
            if (built) return;
            built = true;

            canvas = UIBuild.Screen(GetType().Name, SortOrder);
            canvas.transform.SetParent(transform, false);

            var scrim = UIBuild.Rect("Scrim", canvas.transform, Vector2.zero, Vector2.one,
                                     Vector2.zero, Vector2.zero);
            UIBuild.Fill(scrim, new Color(UISkin.Bark.r * 0.55f, UISkin.Bark.g * 0.55f,
                                          UISkin.Bark.b * 0.55f, ScrimAlpha));

            // Left-aligned column, set in from the edge. Not centred: a centred
            // stack is the single biggest tell of a generated menu.
            Column = UIBuild.Box("Column", canvas.transform, new Vector2(0f, 1f),
                                 new Vector2(0f, 1f), new Vector2(150f, -140f),
                                 new Vector2(900f, 760f));

            var head = UIBuild.Box("Heading", Column, new Vector2(0f, 1f), new Vector2(0f, 1f),
                                   Vector2.zero, new Vector2(900f, 104f));
            UIBuild.FillLabel("Label", head, Heading, 88f, UISkin.Sand,
                              TextAlignmentOptions.TopLeft);
            UIBuild.Rule(Column, new Vector2(0f, 1f), new Vector2(6f, -116f), 300f);

            PopulateBody(Column);

            Menu = new MenuList();
            PopulateMenu(Menu, Column);
        }

        protected void Show()
        {
            EnsureBuilt();
            canvas.gameObject.SetActive(true);
        }

        protected void Hide()
        {
            if (canvas != null) canvas.gameObject.SetActive(false);
        }

        protected virtual void Update()
        {
            if (Visible) Menu?.Tick();
        }

        /// <summary>Convenience: a caption over a value, the readout style used everywhere.</summary>
        protected static TextMeshProUGUI Stat(RectTransform parent, string caption,
                                              string value, Vector2 position,
                                              float valueSize = 56f)
        {
            var capBox = UIBuild.Box("Cap " + caption, parent, new Vector2(0f, 1f),
                                     new Vector2(0f, 1f), position, new Vector2(420f, 26f));
            UIBuild.FillLabel("Label", capBox, caption, 22f, UISkin.SandDim,
                              TextAlignmentOptions.TopLeft);

            var valBox = UIBuild.Box("Val " + caption, parent, new Vector2(0f, 1f),
                                     new Vector2(0f, 1f),
                                     position + new Vector2(-2f, -26f),
                                     new Vector2(460f, valueSize + 12f));
            var label = UIBuild.FillLabel("Label", valBox, value, valueSize, UISkin.Sand,
                                          TextAlignmentOptions.TopLeft);
            UIBuild.Fit(label);
            return label;
        }

        protected static void Tag(RectTransform parent, string text, Vector2 position)
        {
            var box = UIBuild.Box("Tag", parent, new Vector2(0f, 1f), new Vector2(0f, 1f),
                                  position, new Vector2(120f, 42f));
            var skin = UISkin.Load();
            UIBuild.Plate(box, skin != null ? skin.plateRust : null, UISkin.Orange);
            var label = UIBuild.FillLabel("Label", box, text, 26f, UISkin.Sand,
                                          TextAlignmentOptions.Center, 6f);
            // The plate is sized from the words, not the other way round.
            UIBuild.Fit(label, 22f, 5f);
        }
    }
}
