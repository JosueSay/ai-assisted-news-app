import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react';
import { Pressable, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { ImageManipulator, SaveFormat } from 'expo-image-manipulator';

import {
  getBase64DecodedByteLength,
  MAX_ATTENDANCE_PHOTO_BYTES,
} from '../lib/attendancePhoto';
import { colors, radii } from '../theme';

export type CameraCaptureHandle = {
  capture: () => Promise<string | null>;
};

type CameraCaptureProps = {
  style?: StyleProp<ViewStyle>;
};

const compressionProfiles = [
  { maxDimension: 1_280, quality: 0.65 },
  { maxDimension: 960, quality: 0.5 },
  { maxDimension: 720, quality: 0.35 },
  { maxDimension: 480, quality: 0.25 },
] as const;

async function compressAttendancePhoto(
  uri: string,
  originalWidth: number,
  originalHeight: number,
): Promise<string | null> {
  for (const profile of compressionProfiles) {
    const context = ImageManipulator.manipulate(uri);
    let renderedImage: Awaited<ReturnType<typeof context.renderAsync>> | null = null;
    let renderedUri: string | null = null;
    let generatedUri: string | null = null;

    try {
      const dimensionsAreKnown = Number.isFinite(originalWidth)
        && Number.isFinite(originalHeight)
        && originalWidth > 0
        && originalHeight > 0;
      const longestSide = dimensionsAreKnown ? Math.max(originalWidth, originalHeight) : Infinity;
      if (longestSide > profile.maxDimension) {
        context.resize(
          !dimensionsAreKnown || originalWidth >= originalHeight
            ? { width: profile.maxDimension }
            : { height: profile.maxDimension },
        );
      }

      renderedImage = await context.renderAsync();
      const possibleRenderedUri = (renderedImage as unknown as { uri?: unknown }).uri;
      renderedUri = typeof possibleRenderedUri === 'string' ? possibleRenderedUri : null;
      const processed = await renderedImage.saveAsync({
        base64: true,
        compress: profile.quality,
        format: SaveFormat.JPEG,
      });
      generatedUri = processed.uri;

      if (!processed.base64) {
        continue;
      }

      const byteLength = getBase64DecodedByteLength(processed.base64);
      if (byteLength !== null && byteLength <= MAX_ATTENDANCE_PHOTO_BYTES) {
        return `data:image/jpeg;base64,${processed.base64}`;
      }
    } finally {
      if (
        generatedUri?.startsWith('blob:')
        && typeof URL !== 'undefined'
        && typeof URL.revokeObjectURL === 'function'
      ) {
        URL.revokeObjectURL(generatedUri);
      }
      if (
        renderedUri?.startsWith('blob:')
        && typeof URL !== 'undefined'
        && typeof URL.revokeObjectURL === 'function'
      ) {
        URL.revokeObjectURL(renderedUri);
      }
      renderedImage?.release();
      context.release();
    }
  }

  return null;
}

export const CameraCapture = forwardRef<CameraCaptureHandle, CameraCaptureProps>(
  function CameraCapture({ style }, ref) {
    const [permission, requestPermission] = useCameraPermissions();
    const cameraRef = useRef<CameraView>(null);
    const cameraReadyRef = useRef(false);

    useEffect(() => {
      if (permission && !permission.granted && permission.canAskAgain) {
        void requestPermission();
      }
      // Runs once permission status first resolves; re-requesting on every
      // render would spam the OS prompt if the person keeps saying no.
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [Boolean(permission)]);

    useEffect(() => {
      if (!permission?.granted) {
        cameraReadyRef.current = false;
      }
      return () => {
        cameraReadyRef.current = false;
      };
    }, [permission?.granted]);

    useImperativeHandle(ref, () => ({
      async capture() {
        if (!cameraRef.current || !permission?.granted || !cameraReadyRef.current) {
          return null;
        }
        try {
          const photo = await cameraRef.current.takePictureAsync({
            imageType: 'jpg',
            quality: 0.7,
          });
          if (!photo?.uri) {
            return null;
          }

          return await compressAttendancePhoto(photo.uri, photo.width, photo.height);
        } catch (error) {
          console.warn('Attendance photo capture failed', error);
          return null;
        }
      },
    }));

    if (!permission || !permission.granted) {
      return (
        <Pressable
          accessibilityRole="button"
          onPress={() => void requestPermission()}
          style={[styles.box, styles.permissionBox, style]}
        >
          <Text style={styles.permissionIcon}>◎</Text>
          <Text style={styles.permissionText}>Activar cámara</Text>
        </Pressable>
      );
    }

    return (
      <View style={[styles.box, style]}>
        <CameraView
          ref={cameraRef}
          facing="front"
          onCameraReady={() => {
            cameraReadyRef.current = true;
          }}
          onMountError={(mountError) => {
            cameraReadyRef.current = false;
            console.warn('Attendance camera mount failed', mountError.message);
          }}
          style={styles.camera}
        />
      </View>
    );
  },
);

const styles = StyleSheet.create({
  box: {
    borderRadius: radii.medium,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: 'rgba(255,255,255,0.35)',
    backgroundColor: 'rgba(0,0,0,0.2)',
  },
  camera: {
    flex: 1,
  },
  permissionBox: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 6,
    gap: 4,
  },
  permissionIcon: {
    color: colors.white,
    fontSize: 20,
  },
  permissionText: {
    color: colors.white,
    fontSize: 10,
    fontWeight: '700',
    textAlign: 'center',
  },
});
