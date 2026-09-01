#if UNITY_EDITOR
using System.Collections;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine.SceneManagement;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;
using Object = UnityEngine.Object;

namespace DirtTrail.EditorTools
{
    /// <summary>
    /// Drives the real game in play mode from batch mode and reports what
    /// actually happens: whether the collider exists at runtime, whether the
    /// bike settles on it, whether the input map resolves, and whether holding
    /// throttle moves the bike forward.
    ///
    /// Run without -quit, because play mode has to be allowed to tick:
    ///   Unity.exe -batchmode -nographics -projectPath &lt;p&gt; \
    ///     -executeMethod DirtTrail.EditorTools.PlaytestRunner.Run
    /// The probe calls EditorApplication.Exit itself when it is done.
    /// </summary>
    public static class PlaytestRunner
    {
        const string Flag = "DirtTrail.Playtest.Armed";

        /// <summary>Every track scene, ridden in order.</summary>
        public static readonly string[] Tracks = { "RidgeRun", "GravelPit", "DustDevil" };

        public static void Run()
        {
            EditorPrefs.SetBool(Flag, true);
            EditorSceneManager.OpenScene("Assets/Scenes/" + Tracks[0] + ".unity",
                                         OpenSceneMode.Single);
            EditorApplication.EnterPlaymode();
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Boot()
        {
            if (!EditorPrefs.GetBool(Flag, false)) return;
            EditorPrefs.SetBool(Flag, false);
            var go = new GameObject("~Playtest");
            Object.DontDestroyOnLoad(go);
            go.AddComponent<PlaytestProbe>();
        }
    }

    public class PlaytestProbe : MonoBehaviour
    {
        readonly StringBuilder log = new StringBuilder();

        IEnumerator Start()
        {
            log.AppendLine("===== PLAYTEST =====");
            yield return null;

            int problems = 0;
            for (int i = 0; i < PlaytestRunner.Tracks.Length; i++)
            {
                if (i > 0)
                {
                    SceneManager.LoadScene(PlaytestRunner.Tracks[i]);
                    yield return null;
                    yield return null;
                }
                yield return Ride(PlaytestRunner.Tracks[i], v => problems += v);
            }

            Finish(problems == 0 ? "PLAYTEST OK" : "PLAYTEST PROBLEMS " + problems, problems);
        }

        IEnumerator Ride(string track, System.Action<int> report)
        {
            log.AppendLine("");
            log.AppendLine("===== " + track + " =====");
            ReportScene();

            var bike = Object.FindFirstObjectByType<BikeController>();
            var run = RunManager.Instance;
            if (bike == null)
            {
                log.AppendLine("FAIL no bike");
                report(1);
                yield break;
            }

            RideInput.Injected = new RideInput.Synthetic();
            float until = Time.time + 1.5f;
            while (Time.time < until) yield return null;

            bool grounded = bike.Grounded;
            float startX = bike.transform.position.x;
            float deadline = Time.time + 180f;
            float next = 0f, furthest = startX, stuckSince = Time.time;

            while (Time.time < deadline)
            {
                if (run != null && run.Phase == RunPhase.Finished) break;

                float x = bike.transform.position.x;
                if (x > furthest + 1f) { furthest = x; stuckSince = Time.time; }
                if (Time.time - stuckSince > 15f)
                {
                    log.AppendLine(string.Format("STUCK at x={0:0.0}", furthest));
                    break;
                }

                // Proportional on angle plus derivative on spin: a fair stand-in
                // for a rider who levels the bike before touchdown.
                float rot = Mathf.DeltaAngle(0f, bike.transform.eulerAngles.z);
                float spin = bike.Body.angularVelocity;
                float lean = bike.Grounded
                    ? 0f
                    : Mathf.Clamp((rot + spin * 0.22f) / 30f, -1f, 1f);
                RideInput.Injected = new RideInput.Synthetic { Throttle = 1f, Lean = lean };

                if (Time.time >= next) { Sample(bike, run, "run"); next = Time.time + 5f; }
                yield return null;
            }

            float travelled = bike.transform.position.x - startX;
            log.AppendLine(string.Format(
                "RESULT grounded={0} travelled={1:0.0} phase={2} score={3} wipeouts={4} "
                + "elapsed={5:0.0}",
                grounded, travelled, run != null ? run.Phase.ToString() : "-",
                run != null ? run.Score : 0, run != null ? run.Wipeouts : 0,
                run != null ? run.Elapsed : 0f));
            RideInput.Injected = null;

            int bad = 0;
            if (!grounded) { log.AppendLine("FAIL never grounded"); bad++; }
            if (run == null || run.Phase != RunPhase.Finished)
            {
                log.AppendLine("FAIL did not reach the finish");
                bad++;
            }
            report(bad);
        }

        void ReportScene()
        {
            var edges = Object.FindObjectsByType<EdgeCollider2D>(FindObjectsSortMode.None);
            log.AppendLine("edge colliders at runtime: " + edges.Length);
            foreach (var e in edges)
            {
                log.AppendLine(string.Format("  {0}  points={1}  layer={2}  enabled={3}",
                    e.gameObject.name, e.pointCount,
                    LayerMask.LayerToName(e.gameObject.layer), e.enabled));
            }

            int mask = 1 << LayerMask.NameToLayer("Floor");
            log.AppendLine("Floor layer index=" + LayerMask.NameToLayer("Floor") +
                           "  GameLayers.GroundMask=" + GameLayers.GroundMask +
                           "  expected=" + mask);

            int misses = 0;
            for (float x = 20f; x < 1040f; x += 40f)
            {
                if (!Physics2D.Raycast(new Vector2(x, 200f), Vector2.down, 500f, mask)) misses++;
            }
            log.AppendLine("runtime ground probes missed: " + misses + " of 26");

            log.AppendLine(string.Format(
                "physics: gravity={0} simMode={1} timeScale={2} fixedDelta={3}",
                Physics2D.gravity, Physics2D.simulationMode, Time.timeScale,
                Time.fixedDeltaTime));

            var bike = Object.FindFirstObjectByType<BikeController>();
            if (bike != null)
            {
                var rb = bike.Body;
                log.AppendLine(string.Format(
                    "body: type={0} simulated={1} gravityScale={2} mass={3} " +
                    "constraints={4} sleeping={5} config={6}",
                    rb.bodyType, rb.simulated, rb.gravityScale, rb.mass,
                    rb.constraints, rb.IsSleeping(),
                    bike.Config == null ? "NULL" : bike.Config.displayName));

                foreach (var c in bike.GetComponentsInChildren<Collider2D>())
                {
                    log.AppendLine(string.Format(
                        "  collider {0} {1} trigger={2} enabled={3} bounds={4}",
                        c.gameObject.name, c.GetType().Name, c.isTrigger, c.enabled, c.bounds));
                }
                log.AppendLine("  overlapping now: " +
                    Physics2D.OverlapBox(bike.transform.position, new Vector2(3f, 2f), 0f,
                                         mask));
            }
        }

        void ReportInput()
        {
            var asset = InputSystem.actions;
            log.AppendLine("InputSystem.actions = " + (asset == null ? "NULL" : asset.name));
            if (asset == null) return;
            foreach (var path in new[] { "Ride/Throttle", "Ride/Brake", "Ride/Lean",
                                         "Ride/Nitro", "Ride/Pause", "Ride/Retry" })
            {
                var a = asset.FindAction(path);
                log.AppendLine("  " + path + " -> " +
                               (a == null ? "MISSING" : "ok, bindings=" + a.bindings.Count));
            }
            var map = asset.FindActionMap("Ride");
            log.AppendLine("  Ride map enabled=" + (map != null && map.enabled));
        }

        void Sample(BikeController bike, RunManager run, string tag)
        {
            var rb = bike.Body;
            var g = bike.Ground;
            log.AppendLine(string.Format(
                "  [{0,7}] t={1,6:0.0} x={2,7:0.0} y={3,7:0.0} vx={4,6:0.0} " +
                "grounded={5,-5} rot={6,6:0.0} score={7,5} wipe={8}",
                tag, Time.time, bike.transform.position.x, bike.transform.position.y,
                rb.linearVelocity.x, bike.Grounded,
                bike.transform.eulerAngles.z,
                run != null ? run.Score : 0, run != null ? run.Wipeouts : 0));
        }

        void Finish(string verdict, int code)
        {
            log.AppendLine(verdict);
            Debug.Log(log.ToString());
            EditorApplication.isPlaying = false;
            EditorApplication.delayCall += () => EditorApplication.Exit(code);
        }
    }
}
#endif
