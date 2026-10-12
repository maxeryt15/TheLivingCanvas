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
        public List<ItemSave> inventory = new();

        // Mundo
        public List<EaselSave> easels = new();
        public List<FrameSave> frames = new();
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

    /// <summary>Un objeto del inventario. <c>kind</c>: "canvas" (id = tipo de lienzo), "crop" (id + variant) o "painting" (solo entonces se rellena <c>painting</c>).</summary>
    [Serializable]
    public class ItemSave
    {
        public string kind;
        public string id;
        public string variant;
        public int quantity;
        public PaintingSave painting;
    }

    /// <summary>Una pintura (o semilla) guardada; la imagen va en un PNG aparte. <c>crop</c> vacío = sin pintura.</summary>
    [Serializable]
    public class PaintingSave
    {
        public string crop;
        public string variant;
        public string canvasType;
        public string style;
        public bool seed;
        public int generation;
        public int mutation;
        public string image;
        public float score;
        public float spill;
        public float fillShare;
        public int quality;
        public bool canComeToLife;
        public bool cappedByFill;
        public List<ZoneSave> zones = new();
    }

    /// <summary>Resultado de una zona; <c>index</c> es su posición en crop.Template.Zones.</summary>
    [Serializable]
    public class ZoneSave
    {
        public int index;
        public float coverage;
        public float colorFit;
        public Color dominantColor;
    }

    /// <summary>Marco de la galería, por el nombre de su GameObject (solo si está ocupado).</summary>
    [Serializable]
    public class FrameSave
    {
        public string id;
        public PaintingSave painting;
    }
}
