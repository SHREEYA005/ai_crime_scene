using UnityEngine;

public class FPSController : MonoBehaviour
{
    public float moveSpeed = 5f;
    public float mouseSensitivity = 2f;
    private float rotY = 0f;

    void Start() { Cursor.lockState = CursorLockMode.Locked; }

    void Update()
    {
        float mx = Input.GetAxis("Mouse X") * mouseSensitivity;
        float my = Input.GetAxis("Mouse Y") * mouseSensitivity;
        rotY = Mathf.Clamp(rotY - my, -80f, 80f);
        transform.Rotate(0, mx, 0);
        Camera.main.transform.localRotation = Quaternion.Euler(rotY, 0, 0);
        Vector3 move = transform.right * Input.GetAxis("Horizontal") + transform.forward * Input.GetAxis("Vertical");
        transform.position += move * moveSpeed * Time.deltaTime;
        if (Input.GetKeyDown(KeyCode.Escape)) Cursor.lockState = CursorLockMode.None;
    }
}
