using UnityEngine;

public class FPSController : MonoBehaviour
{
    public float moveSpeed = 5f;
    public float mouseSensitivity = 2f;
    private float rotationX = 0f;
    private Transform camTransform;

    void Start()
    {
        Cursor.lockState = CursorLockMode.Locked;
        camTransform = Camera.main.transform;
    }

    void Update()
    {
        // Horizontal rotation — rotate the whole player left/right
        float mouseX = Input.GetAxis("Mouse X") * mouseSensitivity;
        transform.Rotate(0, mouseX, 0);

        // Vertical rotation — only tilt the camera up/down
        float mouseY = Input.GetAxis("Mouse Y") * mouseSensitivity;
        rotationX -= mouseY;
        rotationX = Mathf.Clamp(rotationX, -80f, 80f);
        camTransform.localRotation = Quaternion.Euler(rotationX, 0, 0);

        // WASD movement
        float h = Input.GetAxis("Horizontal");
        float v = Input.GetAxis("Vertical");
        Vector3 move = transform.right * h + transform.forward * v;
        transform.position += move * moveSpeed * Time.deltaTime;

        if (Input.GetKeyDown(KeyCode.Escape))
            Cursor.lockState = CursorLockMode.None;
    }
}
