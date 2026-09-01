using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;

namespace DirtTrail
{
    /// <summary>
    /// Keyboard and gamepad driven vertical menu. Deliberately not built on
    /// Selectable/EventSystem: every screen here is one short list, and this is
    /// less machinery than wiring navigation graphs by hand.
    /// Runs on unscaled time so it still works while the game is paused.
    /// </summary>
    public class MenuList
    {
        readonly List<MenuItem> items = new();
        readonly List<Action> actions = new();

        InputAction navigate, submit, cancel;
        float nextRepeat;
        int held;

        const float FirstRepeat = 0.32f;
        const float NextRepeat = 0.12f;

        public int Index { get; private set; }
        public event Action Cancelled;

        /// <summary>Raised when the highlighted row changes, for screens that preview it.</summary>
        public event Action<int> SelectionChanged;

        public MenuList()
        {
            var asset = InputSystem.actions;
            if (asset == null) return;
            navigate = asset.FindAction("UI/Navigate");
            submit = asset.FindAction("UI/Submit");
            cancel = asset.FindAction("UI/Cancel");

            var map = asset.FindActionMap("UI");
            if (map != null && !map.enabled) map.Enable();
        }

        public void Add(MenuItem item, Action onChosen)
        {
            int index = items.Count;
            items.Add(item);
            actions.Add(onChosen);
            item.SetSelected(index == Index);

            if (item.Pointer != null)
            {
                item.Pointer.Index = index;
                item.Pointer.Hovered += Select;
                item.Pointer.Clicked += i => { Select(i); Activate(); };
            }
        }

        public void Select(int index)
        {
            if (items.Count == 0) return;
            index = ((index % items.Count) + items.Count) % items.Count;
            if (index == Index && items[index] != null) return;

            Index = index;
            for (int i = 0; i < items.Count; i++) items[i].SetSelected(i == Index);
            SelectionChanged?.Invoke(Index);
        }

        public void Tick()
        {
            if (items.Count == 0) return;

            float y = navigate != null ? navigate.ReadValue<Vector2>().y : 0f;
            int dir = Mathf.Abs(y) < 0.5f ? 0 : (y > 0f ? -1 : 1);   // up moves toward index 0

            if (dir == 0)
            {
                held = 0;
            }
            else if (dir != held)
            {
                held = dir;
                Step(dir);
                nextRepeat = Time.unscaledTime + FirstRepeat;
            }
            else if (Time.unscaledTime >= nextRepeat)
            {
                Step(dir);
                nextRepeat = Time.unscaledTime + NextRepeat;
            }

            if (submit != null && submit.WasPressedThisFrame()) Activate();
            if (cancel != null && cancel.WasPressedThisFrame()) Cancelled?.Invoke();
        }

        void Step(int dir)
        {
            int next = Index + dir;
            Select(next);
        }

        public void Activate()
        {
            if (Index < 0 || Index >= actions.Count) return;
            actions[Index]?.Invoke();
        }
    }
}
