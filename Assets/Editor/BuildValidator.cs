#if UNITY_EDITOR
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace DirtTrail.EditorTools
{
    /// <summary>
    /// Batch-mode smoke test: opens every scene in the build list and reports
    /// missing scripts, unresolved sprite references and empty Resources.
    /// Run with -executeMethod DirtTrail.EditorTools.BuildValidator.Validate
    /// </summary>
    public static class BuildValidator
    {
        public static void Validate()
        {
            var log = new StringBuilder();
            int problems = 0;

            foreach (var scene in EditorBuildSettings.scenes)
            {
                var opened = EditorSceneManager.OpenScene(scene.path, OpenSceneMode.Single);
                log.AppendLine("SCENE " + opened.name + "  roots=" +
                               opened.GetRootGameObjects().Length);

                foreach (var root in opened.GetRootGameObjects())
                {
                    foreach (var mb in root.GetComponentsInChildren<MonoBehaviour>(true))
                    {
                        if (mb == null)
                        {
                            log.AppendLine("  MISSING SCRIPT under " + root.name);
                            problems++;
                        }
                    }
                    foreach (var sr in root.GetComponentsInChildren<SpriteRenderer>(true))
                    {
                        if (sr.sprite == null)
                        {
                            log.AppendLine("  NO SPRITE on " + Path(sr.transform));
                            problems++;
                        }
                    }
                }
            }

            problems += CheckTrack(log);

            foreach (var name in new[] { "BikeRoster", "UISkin", "FxKit" })
            {
                if (Resources.Load<ScriptableObject>(name) == null)
                {
                    log.AppendLine("MISSING RESOURCE " + name);
                    problems++;
                }
            }

            var roster = Resources.Load<BikeRoster>("BikeRoster");
            if (roster != null)
            {
                log.AppendLine("ROSTER count=" + roster.Count);
                for (int i = 0; i < roster.Count; i++)
                {
                    var b = roster[i];
                    if (b == null || b.body == null || b.rider == null ||
                        b.wheelFront == null || b.wheelRear == null)
                    {
                        log.AppendLine("  INCOMPLETE BIKE at " + i);
                        problems++;
                    }
                    else log.AppendLine("  BIKE " + b.displayName + " ok");
                }
            }

            log.AppendLine(problems == 0 ? "VALIDATE OK" : "VALIDATE PROBLEMS " + problems);
            Debug.Log(log.ToString());
            if (Application.isBatchMode) EditorApplication.Exit(problems == 0 ? 0 : 2);
        }

        /// <summary>
        /// The track scene, its collider and the bike spawn are all authored by
        /// hand from the same profile. This is the check that they agree: cast
        /// down from the bike and from a handful of points along the track, and
        /// insist on hitting ground every time.
        /// </summary>
        static int CheckTrack(StringBuilder log)
        {
            EditorSceneManager.OpenScene("Assets/Scenes/RidgeRun.unity", OpenSceneMode.Single);
            int problems = 0;

            var bike = Object.FindFirstObjectByType<BikeController>();
            if (bike == null)
            {
                log.AppendLine("NO BIKE in RidgeRun");
                return 1;
            }

            var sensor = bike.GetComponent<GroundSensor>();
            var body = bike.GetComponent<Rigidbody2D>();
            log.AppendLine("BIKE at " + bike.transform.position +
                           "  rb=" + (body != null) + "  sensor=" + (sensor != null));
            if (sensor == null || body == null) problems++;

            int mask = 1 << LayerMask.NameToLayer("Floor");
            var edge = Object.FindFirstObjectByType<EdgeCollider2D>();
            if (edge == null || edge.pointCount < 100)
            {
                log.AppendLine("TERRAIN COLLIDER missing or too coarse");
                problems++;
            }
            else
            {
                log.AppendLine("TERRAIN collider points=" + edge.pointCount +
                               " layer=" + LayerMask.LayerToName(edge.gameObject.layer));
                if (edge.gameObject.layer != LayerMask.NameToLayer("Floor")) problems++;
            }

            // Straight down from the spawn, then along the track at intervals.
            float spawnDrop = Probe(bike.transform.position, mask);
            log.AppendLine("SPAWN drop=" + spawnDrop.ToString("0.00"));
            if (spawnDrop < 0f || spawnDrop > 6f) problems++;

            int misses = 0;
            for (float x = 20f; x < 1040f; x += 40f)
            {
                if (Probe(new Vector2(x, 200f), mask) < 0f) misses++;
            }
            log.AppendLine("TRACK probes missed=" + misses);
            problems += misses;

            return problems;
        }

        static float Probe(Vector2 from, int mask)
        {
            var hit = Physics2D.Raycast(from, Vector2.down, 500f, mask);
            return hit ? hit.distance : -1f;
        }

        static string Path(Transform t)
        {
            var s = t.name;
            while (t.parent != null) { t = t.parent; s = t.name + "/" + s; }
            return s;
        }
    }
}
#endif
