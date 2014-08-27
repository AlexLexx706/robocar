package com.example.bluetooth1;

import java.io.IOException;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

import android.util.Log;

public class Protocol {
	private final static String TAG = "Protocol";
	
	private final static byte CMD_SetLeftWheelPower = 0;
	private final static byte CMD_SetRightWheelPower = 1;
	private final static byte CMD_SetWheelsPower = 2;
	private final static byte CMD_SetPowerZerro = 3;
	private final static byte CMD_StartWalk = 4;
	private final static byte CMD_SetPidSettings = 5;
	private final static byte CMD_SetAngle = 6;
	private final static byte CMD_ENABLE_DEBUG = 7;
	
	OutputStream outStream;
	
	public Protocol(OutputStream outStream) {
		this.outStream = outStream;
	}

	public void set_left_wheel_power(float l_p) {
		Log.d(TAG, "set_left_wheel_power l_p:");
		try {
			ByteBuffer buffer = ByteBuffer.allocate(10);
			buffer.order(ByteOrder.LITTLE_ENDIAN);
			buffer.put(CMD_SetLeftWheelPower);
			buffer.putFloat(l_p);
			outStream.write(buffer.position());
			outStream.write(buffer.array(), 0, buffer.position());
			outStream.flush();
		} catch (IOException e) {
			Log.e(TAG, e.getMessage());
		}
	}	

	public void set_right_wheel_power(float r_p) {
		Log.d(TAG, "set_right_wheel_power r_p:");
		try {
			ByteBuffer buffer = ByteBuffer.allocate(10);
			buffer.order(ByteOrder.LITTLE_ENDIAN);
			buffer.put(CMD_SetRightWheelPower);
			buffer.putFloat(r_p);
			outStream.write(buffer.position());
			outStream.write(buffer.array(), 0, buffer.position());
			outStream.flush();
		} catch (IOException e) {
			Log.e(TAG, e.getMessage());
		}
	}	

	
	public void set_wheels_power(float l_p, float r_p) {
		Log.d(TAG, "set_wheels_power l_p:" + l_p + " r_p:" + r_p);
		try {
			ByteBuffer buffer = ByteBuffer.allocate(10);
			buffer.order(ByteOrder.LITTLE_ENDIAN);
			buffer.put(CMD_SetWheelsPower);
			buffer.putFloat(l_p);
			buffer.putFloat(r_p);
			outStream.write(buffer.position());
			outStream.write(buffer.array(), 0, buffer.position());
			outStream.flush();
		} catch (IOException e) {
			Log.e(TAG, e.getMessage());
		}
	}	
	public void set_power_zerro() {
		Log.d(TAG, "set_power_zerro");

		try {
			ByteBuffer buffer = ByteBuffer.allocate(10);
			buffer.order(ByteOrder.LITTLE_ENDIAN);
			buffer.put(CMD_SetPowerZerro);
			outStream.write(buffer.position());
			outStream.write(buffer.array(), 0, buffer.position());
			outStream.flush();
		} catch (IOException e) {
			Log.e(TAG, e.getMessage());
		}
	}
	
	public void start_walk() {
		Log.d(TAG, "start_walk");

		try {
			ByteBuffer buffer = ByteBuffer.allocate(10);
			buffer.order(ByteOrder.LITTLE_ENDIAN);
			buffer.put(CMD_StartWalk);
			outStream.write(buffer.position());
			outStream.write(buffer.array(), 0, buffer.position());
			outStream.flush();
		} catch (IOException e) {
			Log.e(TAG, e.getMessage());
		}
	}
	
	public void set_pid_settings(float p, float i, float d) {
		Log.d(TAG, "set_pid_settings p:" + p + " i:" + i + " d:" + d);
		try {
			ByteBuffer buffer = ByteBuffer.allocate(20);
			buffer.order(ByteOrder.LITTLE_ENDIAN);
			buffer.put(CMD_SetPidSettings);
			buffer.putFloat(p);
			buffer.putFloat(i);
			buffer.putFloat(d);
			outStream.write(buffer.position());
			outStream.write(buffer.array(), 0, buffer.position());
			outStream.flush();
		} catch (IOException e) {
			Log.e(TAG, e.getMessage());
		}
	}

	public void set_angle(float angle) {
		Log.d(TAG, "send_set_angle angle:" + angle);
		try {
			ByteBuffer buffer = ByteBuffer.allocate(10);
			buffer.order(ByteOrder.LITTLE_ENDIAN);
			buffer.put(CMD_SetAngle);
			buffer.putFloat(angle);
			outStream.write(buffer.position());
			outStream.write(buffer.array(), 0, buffer.position());
			outStream.flush();
		} catch (IOException e) {
			Log.e(TAG, e.getMessage());
		}
	}
	
	public void enable_debug(boolean enable) {
		Log.d(TAG, "ebanle_debug enable:" + enable);
		try {
			ByteBuffer buffer = ByteBuffer.allocate(10);
			buffer.order(ByteOrder.LITTLE_ENDIAN);
			buffer.put(CMD_ENABLE_DEBUG);
			buffer.put(enable == true ? (byte)1 : (byte)0);
			outStream.write(buffer.position());
			outStream.write(buffer.array(), 0, buffer.position());
			outStream.flush();
		} catch (IOException e) {
			Log.e(TAG, e.getMessage());
		}
	}
}
