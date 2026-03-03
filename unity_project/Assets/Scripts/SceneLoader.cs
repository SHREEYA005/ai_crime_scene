using UnityEngine;
using System.IO;

public class SceneLoader : MonoBehaviour
{
    public GameObject defaultPrefab;
    public GameObject[] namedPrefabs;

    void Start()
    {
        string path = Path.Combine(Application.streamingAssetsPath, "scene_data.json");
        if (!File.Exists(path)) { Debug.LogError("scene_data.json not found in StreamingAssets!"); return; }
        SceneData data = JsonUtility.FromJson<SceneData>(File.ReadAllText(path));
        foreach (var obj in data.objects)
        {
            GameObject prefab = FindPrefab(obj.prefab) ?? defaultPrefab;
            if (prefab == null) continue;
            var instance = Instantiate(prefab,
                new Vector3(obj.position.x, obj.position.y, obj.position.z),
                Quaternion.Euler(obj.rotation.x, obj.rotation.y, obj.rotation.z));
            instance.name = $"{obj.label}_{obj.id}";
            AddLabel(instance, obj.label, obj.confidence);
        }
    }

    GameObject FindPrefab(string name)
    {
        if (namedPrefabs == null) return null;
        foreach (var p in namedPrefabs) if (p != null && p.name == name) return p;
        return null;
    }

    void AddLabel(GameObject obj, string label, float confidence)
    {
        var lo = new GameObject("Label");
        lo.transform.SetParent(obj.transform);
        lo.transform.localPosition = new Vector3(0, 1.5f, 0);
        var tm = lo.AddComponent<TextMesh>();
        tm.text = confidence > 0 ? $"{label}\n{Mathf.Round(confidence*100)}%" : label;
        tm.fontSize = 24; tm.color = Color.white;
        tm.anchor = TextAnchor.MiddleCenter;
    }
}

[System.Serializable] public class SceneData { public string case_id; public string case_title; public SceneObject[] objects; }
[System.Serializable] public class SceneObject { public int id; public string label; public string prefab; public float confidence; public Vec3 position; public Vec3 rotation; }
[System.Serializable] public class Vec3 { public float x, y, z; }
