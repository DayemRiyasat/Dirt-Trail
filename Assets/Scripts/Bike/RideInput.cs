using UnityEngine;
using UnityEngine.InputSystem;

namespace DirtTrail
{
    /// <summary>
    /// One place that touches the Input System. Everything else reads plain
    /// floats and bools, so the controller never has to care about devices.
    /// Actions are resolved once; a missing action degrades to neutral input
    /// rather than throwing, which keeps a half-configured project playable.
    /// </summary>
    public static class RideInput
    {
        static InputAction throttle, brake, lean, nitro, pause, retry;
        static bool resolved;

#if UNITY_EDITOR
        /// <summary>
        /// Editor-only test seam. Batch mode cannot drive the Input System's
        /// action layer, so the automated playtest injects control values here
        /// instead. Compiled out of every build.
        /// </summary>
        public struct Synthetic
        {
            public float Throttle, Brake, Lean;
        }

        public static Synthetic? Injected;
#endif

        public static void Resolve()
        {
            if (resolved) return;
            resolved = true;

            var asset = InputSystem.actions;
            if (asset == null)
            {
                Debug.LogWarning("RideInput: no project-wide input actions asset assigned.");
                return;
            }

            throttle = asset.FindAction("Ride/Throttle");
            brake = asset.FindAction("Ride/Brake");
            lean = asset.FindAction("Ride/Lean");
            nitro = asset.FindAction("Ride/Nitro");
            pause = asset.FindAction("Ride/Pause");
            retry = asset.FindAction("Ride/Retry");

            var map = asset.FindActionMap("Ride");
            if (map != null && !map.enabled) map.Enable();
        }

        static bool Pressed(InputAction a) => a != null && a.WasPressedThisFrame();

        /// <summary>
        /// Reads a held control as a value rather than asking the action whether
        /// it is "pressed". An axis value reflects the control right now, which
        /// is what a per-frame poll wants; the button-phase check is kept as a
        /// fallback so either mechanism is enough on its own.
        /// </summary>
        static float Axis(InputAction a)
        {
            if (a == null) return 0f;
            float v = Mathf.Abs(a.ReadValue<float>());
            if (v < 0.01f && a.IsPressed()) v = 1f;
            return Mathf.Clamp01(v);
        }

        /// <summary>0..1. A key gives 1, a trigger gives its travel.</summary>
        public static float Throttle
        {
            get
            {
#if UNITY_EDITOR
                if (Injected.HasValue) return Injected.Value.Throttle;
#endif
                Resolve();
                return Axis(throttle);
            }
        }

        public static float Brake
        {
            get
            {
#if UNITY_EDITOR
                if (Injected.HasValue) return Injected.Value.Brake;
#endif
                Resolve();
                return Axis(brake);
            }
        }

        /// <summary>-1 lifts the nose (backflip), +1 drops it (frontflip).</summary>
        public static float Lean
        {
            get
            {
#if UNITY_EDITOR
                if (Injected.HasValue) return Injected.Value.Lean;
#endif
                Resolve();
                if (lean == null) return 0f;
                float v = lean.ReadValue<float>();
                return Mathf.Abs(v) < 0.15f ? 0f : Mathf.Clamp(v, -1f, 1f);
            }
        }

        public static bool NitroPressed { get { Resolve(); return Pressed(nitro); } }
        public static bool PausePressed { get { Resolve(); return Pressed(pause); } }
        public static bool RetryPressed { get { Resolve(); return Pressed(retry); } }

        /// <summary>Scene loads invalidate the cached actions.</summary>
        public static void Forget()
        {
            resolved = false;
            throttle = brake = lean = nitro = pause = retry = null;
        }
    }
}
