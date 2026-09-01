using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// Picks which burst to throw up. Pools are walked with a random stride
    /// rather than sampled, so you never see the same word twice running and
    /// never a long gap without one.
    /// </summary>
    public static class Shout
    {
        static readonly int[] cursors = new int[7];

        static Sprite Next(Sprite[] pool, int slot)
        {
            if (pool == null || pool.Length == 0) return null;
            if (pool.Length == 1) return pool[0];
            cursors[slot] = (cursors[slot] + Random.Range(1, pool.Length)) % pool.Length;
            return pool[cursors[slot]];
        }

        public static Sprite ForFlip(int rotations)
        {
            var kit = ShoutKit.Load();
            if (kit == null) return null;
            return rotations >= 2 ? Next(kit.bigFlip, 1) : Next(kit.flip, 0);
        }

        public static Sprite ForAir()
        {
            var kit = ShoutKit.Load();
            return kit == null ? null : Next(kit.air, 2);
        }

        public static Sprite ForPerfect()
        {
            var kit = ShoutKit.Load();
            return kit == null ? null : Next(kit.perfect, 3);
        }

        public static Sprite ForWipeout()
        {
            var kit = ShoutKit.Load();
            return kit == null ? null : Next(kit.wipeout, 4);
        }

        public static Sprite ForPickup(PickupKind kind)
        {
            var kit = ShoutKit.Load();
            if (kit == null) return null;
            return kind == PickupKind.Nitro ? Next(kit.nitro, 5) : Next(kit.airPickup, 6);
        }
    }
}
