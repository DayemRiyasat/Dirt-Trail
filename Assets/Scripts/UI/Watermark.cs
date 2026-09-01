using TMPro;
using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// Credit line, bottom right of every screen. Its own canvas at a high sort
    /// order so it sits above the HUD and the pause and results overlays, and
    /// with nothing raycastable on it so it never eats a click.
    /// </summary>
    public class Watermark : MonoBehaviour
    {
        [SerializeField] string text = "Made by Dayem R.";

        [Range(0.2f, 1f)]
        [SerializeField] float opacity = 0.55f;

        [SerializeField] float size = 20f;

        void Start()
        {
            var canvas = UIBuild.Screen("Watermark", 200);
            canvas.transform.SetParent(transform, false);

            var box = UIBuild.Box("Credit", canvas.transform, new Vector2(1f, 0f),
                                  new Vector2(1f, 0f), new Vector2(-26f, 18f),
                                  new Vector2(180f, size + 8f));

            var colour = new Color(UISkin.SandDim.r, UISkin.SandDim.g, UISkin.SandDim.b,
                                   opacity);
            var label = UIBuild.FillLabel("Label", box, text, size, colour,
                                          TextAlignmentOptions.BottomRight);
            label.characterSpacing = 4f;
            UIBuild.Fit(label, 6f, 2f);
        }
    }
}
