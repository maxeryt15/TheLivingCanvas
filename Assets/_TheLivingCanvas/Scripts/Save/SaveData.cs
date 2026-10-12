using System;
using System.Collections.Generic;
using UnityEngine;

namespace TheLivingCanvas.Save
{
    /// <summary>Contenido de la partida guardada (JSON vía JsonUtility: solo campos y listas). Los campos nuevos reciben su valor por defecto al leer partidas viejas.</summary>
    [Serializable]
    public class SaveData
    {
        public const int CurrentVersion = 1;

        public int version = CurrentVersion;

        // Economía y progreso
        public int coins;
        public int xp;
        public List<string> discovered = new();
        public List<string> claimedSets = new();

        // Lo que sabe y tiene el jugador
        public List<string> knownCrops = new();
        public List<string> knownStyles = new();
        public List<AmountEntry> pigments = new();
        public List<string> palette = new();
        public List<string> brushes = new();
        public List<string> tools = new();

        // Mundo
        public List<EaselSave> easels = new();
        public int season;
        public int day;
        public int year;
        public float minutesOfDay;
        public List<NpcSave> npcs = new();
        public int boardCommissionIndex;
        public List<bool> festivalWon = new();

        // Jugador
        public Vector3 playerPosition;
        public float playerYaw;
    }

    /// <summary>Una cantidad por id (ej. unidades de un pigmento).</summary>
    [Serializable]
    public class AmountEntry
    {
        public string id;
        public int amount;
    }

    /// <summary>Estado de un caballete, por el nombre de su GameObject.</summary>
    [Serializable]
    public class EaselSave
    {
        public string id;
        public int width;
        public int height;
    }

    /// <summary>Estado de un personaje, por el nombre de su NpcDefinition.</summary>
    [Serializable]
    public class NpcSave
    {
        public string id;
        public int commissionIndex;
        public bool requested;
    }
}
