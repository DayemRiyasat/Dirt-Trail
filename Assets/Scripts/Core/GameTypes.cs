namespace DirtTrail
{
    /// <summary>Layer names, resolved once instead of by string at every callsite.</summary>
    public static class GameLayers
    {
        public const string GroundName = "Floor";
        public const string RiderName = "Player";

        public static readonly int Ground = UnityEngine.LayerMask.NameToLayer(GroundName);
        public static readonly int Rider = UnityEngine.LayerMask.NameToLayer(RiderName);

        public static readonly int GroundMask = 1 << Ground;
        public static readonly int RiderMask = 1 << Rider;

        public static bool IsGround(int layer) => layer == Ground;
        public static bool IsRider(int layer) => layer == Rider;
    }

    public enum TrickType
    {
        None,
        BackFlip,
        FrontFlip,
    }

    /// <summary>How square the bike was to the ground on touchdown.</summary>
    public enum LandingQuality
    {
        Wipeout,
        Rough,
        Clean,
        Perfect,
    }

    public enum PickupKind
    {
        Nitro,
        AirControl,
    }

    public enum RunPhase
    {
        Ready,
        Riding,
        Paused,
        Finished,
        Wiped,
    }

    /// <summary>Why a run ended, which decides what the results screen says.</summary>
    public enum RunOutcome
    {
        None,
        Finished,
        Retired,
    }
}
