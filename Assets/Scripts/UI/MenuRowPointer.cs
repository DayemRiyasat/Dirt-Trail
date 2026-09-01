using System;
using UnityEngine;
using UnityEngine.EventSystems;

namespace DirtTrail
{
    /// <summary>
    /// Makes a menu row respond to the mouse. Hovering moves the same highlight
    /// the keyboard uses, so the two input methods share one notion of what is
    /// selected instead of fighting over it.
    /// </summary>
    public class MenuRowPointer : MonoBehaviour, IPointerEnterHandler, IPointerClickHandler
    {
        public int Index { get; set; }

        public event Action<int> Hovered;
        public event Action<int> Clicked;

        public void OnPointerEnter(PointerEventData eventData) => Hovered?.Invoke(Index);

        public void OnPointerClick(PointerEventData eventData) => Clicked?.Invoke(Index);
    }
}
