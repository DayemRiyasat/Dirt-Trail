using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace DirtTrail
{
    /// <summary>
    /// Small factory for the interface. Screens are assembled in code from these
    /// pieces so there is one definition of what a label, a plate and a rule look
    /// like, and no chance of two screens drifting apart in a prefab.
    ///
    /// House style: caps, letterspaced, left-aligned. Flat plates with a cut
    /// edge, never a rounded pill. One accent colour, used sparingly.
    /// </summary>
    public static class UIBuild
    {
        public const float Tracking = 12f;      // TMP character spacing, caps need it

        public static Canvas Screen(string name, int sortOrder = 0)
        {
            var go = new GameObject(name, typeof(Canvas), typeof(CanvasScaler),
                                    typeof(GraphicRaycaster));
            var canvas = go.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = sortOrder;

            var scaler = go.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920f, 1080f);
            scaler.matchWidthOrHeight = 0.5f;
            return canvas;
        }

        public static RectTransform Rect(string name, Transform parent,
                                         Vector2 anchorMin, Vector2 anchorMax,
                                         Vector2 offsetMin, Vector2 offsetMax)
        {
            var go = new GameObject(name, typeof(RectTransform));
            var rt = go.GetComponent<RectTransform>();
            rt.SetParent(parent, false);
            rt.anchorMin = anchorMin;
            rt.anchorMax = anchorMax;
            rt.offsetMin = offsetMin;
            rt.offsetMax = offsetMax;
            return rt;
        }

        /// <summary>A box of a fixed size pinned to one anchor point.</summary>
        public static RectTransform Box(string name, Transform parent, Vector2 anchor,
                                        Vector2 pivot, Vector2 position, Vector2 size)
        {
            var rt = Rect(name, parent, anchor, anchor, Vector2.zero, Vector2.zero);
            rt.pivot = pivot;
            rt.anchoredPosition = position;
            rt.sizeDelta = size;
            return rt;
        }

        public static Image Plate(RectTransform rt, Sprite sprite, Color tint)
        {
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = sprite;
            img.type = sprite != null ? Image.Type.Sliced : Image.Type.Simple;
            img.color = tint;
            img.raycastTarget = false;
            return img;
        }

        public static Image Fill(RectTransform rt, Color tint)
        {
            var img = rt.gameObject.AddComponent<Image>();
            img.color = tint;
            img.raycastTarget = false;
            return img;
        }

        public static TextMeshProUGUI Label(string name, Transform parent, string text,
                                            float size, Color color,
                                            TextAlignmentOptions align = TextAlignmentOptions.Left,
                                            FontStyles style = FontStyles.Bold)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);

            var tmp = go.AddComponent<TextMeshProUGUI>();
            var skin = UISkin.Load();
            if (skin != null && skin.Font != null) tmp.font = skin.Font;

            tmp.text = text;
            tmp.fontSize = size;
            tmp.color = color;
            tmp.alignment = align;
            tmp.fontStyle = style;
            tmp.characterSpacing = Tracking;
            tmp.textWrappingMode = TextWrappingModes.NoWrap;
            tmp.raycastTarget = false;
            return tmp;
        }

        /// <summary>Stretch a label over its parent with a small inset.</summary>
        public static TextMeshProUGUI FillLabel(string name, RectTransform parent, string text,
                                                float size, Color color,
                                                TextAlignmentOptions align, float inset = 0f)
        {
            var tmp = Label(name, parent, text, size, color, align);
            var rt = tmp.rectTransform;
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = new Vector2(inset, inset);
            rt.offsetMax = new Vector2(-inset, -inset);
            return tmp;
        }

        /// <summary>
        /// A solid plate behind a block of copy. The menus sit over the live
        /// world, and sand-coloured text on sunlit dirt is close to invisible;
        /// this puts the type back on a ground it can hold against.
        /// </summary>
        public static Image Panel(Transform parent, Vector2 position, Vector2 size,
                                  float alpha = 0.93f)
        {
            var rt = Box("Panel", parent, new Vector2(0f, 1f), new Vector2(0f, 1f),
                         position, size);
            var skin = UISkin.Load();
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = skin != null ? skin.plateDark : null;
            img.type = img.sprite != null ? Image.Type.Sliced : Image.Type.Simple;
            img.color = new Color(UISkin.Bark.r, UISkin.Bark.g, UISkin.Bark.b, alpha);
            img.raycastTarget = false;
            return img;
        }

        /// <summary>
        /// Grows a label's box until the box actually holds the text.
        ///
        /// Boxes are authored at a guessed size, and any text longer than the
        /// guess spills over its own plate. Measuring the text and growing the
        /// box means a border always reaches the end of what is written on it,
        /// whatever the copy turns out to be. It never shrinks, so a row of
        /// boxes keeps whatever alignment it was given.
        /// </summary>
        public static void Fit(TextMeshProUGUI label, float padX = 0f, float padY = 0f)
        {
            if (label == null) return;
            var box = label.rectTransform.parent as RectTransform;
            if (box == null) return;

            label.ForceMeshUpdate();
            Vector2 want = label.GetPreferredValues(label.text, 0f, 0f);
            box.sizeDelta = new Vector2(Mathf.Max(box.sizeDelta.x, want.x + padX * 2f),
                                        Mathf.Max(box.sizeDelta.y, want.y + padY * 2f));
        }

        /// <summary>Re-measures a fitted plate after its content changed.</summary>
        public static void RefitPanel(Image panel, RectTransform column, float padding = 36f)
        {
            if (panel == null || column == null) return;
            Canvas.ForceUpdateCanvases();
            var bounds = RectTransformUtility.CalculateRelativeRectTransformBounds(column);
            panel.rectTransform.anchoredPosition = column.anchoredPosition +
                new Vector2(bounds.min.x - padding, bounds.max.y + padding);
            panel.rectTransform.sizeDelta =
                new Vector2(bounds.size.x, bounds.size.y) + Vector2.one * (padding * 2f);
        }

        /// <summary>
        /// Fits a plate around whatever a column ended up containing.
        ///
        /// Hand-picked panel sizes go stale the moment a label changes - a bike
        /// blurb, a longer title - and the text then runs off the edge of its
        /// own box. Measuring the built content instead means the plate is
        /// always big enough, whatever the copy says.
        /// </summary>
        public static Image PanelBehind(RectTransform column, float padding = 36f,
                                        float alpha = 0.93f)
        {
            Canvas.ForceUpdateCanvases();
            var bounds = RectTransformUtility.CalculateRelativeRectTransformBounds(column);

            // The column is anchored and pivoted top-left, so its local origin
            // is its top-left corner and the bounds are offsets from there.
            var position = column.anchoredPosition +
                           new Vector2(bounds.min.x - padding, bounds.max.y + padding);
            var size = new Vector2(bounds.size.x, bounds.size.y) + Vector2.one * (padding * 2f);

            var img = Panel(column.parent, position, size, alpha);
            img.rectTransform.SetAsFirstSibling();
            return img;
        }

        /// <summary>The accent rule that sits under a heading. Tiles on X.</summary>
        public static Image Rule(Transform parent, Vector2 anchor, Vector2 position,
                                 float width, float height = 10f)
        {
            var rt = Box("Rule", parent, anchor, new Vector2(0f, 0.5f), position,
                         new Vector2(width, height));
            var skin = UISkin.Load();
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = skin != null ? skin.stripe : null;
            img.type = Image.Type.Tiled;
            img.color = Color.white;
            img.raycastTarget = false;
            return img;
        }

        /// <summary>
        /// A menu row: chevron marker, label, no box. Selection is shown by the
        /// chevron and a colour shift, not by a highlighted panel.
        /// </summary>
        public static MenuItem Row(Transform parent, string text, Vector2 position,
                                   float width = 620f, float height = 74f)
        {
            var rt = Box("Row " + text, parent, new Vector2(0f, 1f), new Vector2(0f, 1f),
                         position, new Vector2(width, height));

            // An all-but-invisible graphic, purely so the raycaster can find the
            // row. Alpha zero would not be hit-tested, so it sits just above it.
            var hit = rt.gameObject.AddComponent<Image>();
            hit.color = new Color(1f, 1f, 1f, 0.004f);
            hit.raycastTarget = true;
            var pointer = rt.gameObject.AddComponent<MenuRowPointer>();

            var skin = UISkin.Load();
            var markRt = Box("Mark", rt, new Vector2(0f, 0.5f), new Vector2(0f, 0.5f),
                             new Vector2(6f, 0f), new Vector2(30f, 30f));
            var mark = markRt.gameObject.AddComponent<Image>();
            mark.sprite = skin != null ? skin.chevron : null;
            mark.color = UISkin.Orange;
            mark.raycastTarget = false;

            var label = Label("Text", rt, text, 46f, UISkin.SandDim);
            var lrt = label.rectTransform;
            lrt.anchorMin = new Vector2(0f, 0f);
            lrt.anchorMax = new Vector2(1f, 1f);
            lrt.offsetMin = new Vector2(52f, 0f);
            lrt.offsetMax = new Vector2(0f, 0f);
            label.alignment = TextAlignmentOptions.Left;

            return new MenuItem(rt, label, mark, pointer);
        }
    }

    /// <summary>One selectable line in a menu.</summary>
    public class MenuItem
    {
        public readonly RectTransform Root;
        public readonly TextMeshProUGUI Label;
        public readonly Image Marker;
        public readonly MenuRowPointer Pointer;

        public MenuItem(RectTransform root, TextMeshProUGUI label, Image marker,
                        MenuRowPointer pointer = null)
        {
            Root = root;
            Label = label;
            Marker = marker;
            Pointer = pointer;
            SetSelected(false);
        }

        public void SetSelected(bool selected)
        {
            if (Marker != null) Marker.enabled = selected;
            if (Label != null)
            {
                Label.color = selected ? UISkin.Sand : UISkin.SandDim;
                Label.rectTransform.offsetMin =
                    new Vector2(selected ? 52f : 40f, Label.rectTransform.offsetMin.y);
            }
        }
    }
}
