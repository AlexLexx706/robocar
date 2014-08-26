package com.example.bluetooth1;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import android.app.Activity;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.text.Layout;
import android.text.method.ScrollingMovementMethod;
import android.util.Log;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.RelativeLayout;
import android.widget.SeekBar;
import android.widget.Spinner;
import android.widget.TextView;
 
public class MainActivity extends Activity {
  private static final String TAG = "bluetooth1";
   
  Button btnOn, btnOff;
   
  private static final int REQUEST_ENABLE_BT = 1;
  private BluetoothAdapter btAdapter = null;
  private BluetoothSocket btSocket = null;
  private OutputStream outStream = null;
  private InputStream in_stream = null;
  private Spinner spinner_device_list;
  private SeekBar seekBar_angle;
  private RelativeLayout controlls;
  private Button button_connect;
  private Handler handler;
  private TextView textView_messages;
  private Thread read_thread = null;
  
  public final int MESSAGE_READ = 1;

  // SPP UUID сервиса 
  private static final UUID MY_UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");
  
  class ReadThread extends Thread{
	  Handler handler;
	  
	  public ReadThread(Handler handler){
		  
		  this.handler = handler;
	  }

	  public void run () {
		  Log.d(TAG, "Begin read_thread");
		  
		  byte [] buffer = new byte[1024];
		  int bytes;
		  
		  while (!isInterrupted()) {
			  try {
				  bytes = in_stream.read(buffer);
				  
				  if (bytes >= 0) {
					  byte [] message = new byte[bytes];
					  System.arraycopy(buffer, 0, message, 0, message.length);
					  handler.sendMessage(handler.obtainMessage(MESSAGE_READ, message));
				  }
				  else if (bytes == -1 ){
					  break;
				  }
			  } catch (Exception e) {
				  Log.e(TAG, e.getMessage());
				  break;
			  }
		  }
		  Log.d(TAG, "End read_thread");
	  }
  }
  
  List<String> get_paired_device_list() {
	  List<String> list = new ArrayList<String>();
	  if (btAdapter != null) {
		  Set<BluetoothDevice> pairedDevices = btAdapter.getBondedDevices();
		  //If there are paired devices
		  if (pairedDevices.size() > 0) {
			  // Loop through paired devices
			  for (BluetoothDevice device : pairedDevices) {
				  // Add the name and address to an array adapter to show in a ListView
				  list.add(device.getName() + "\n" + device.getAddress());
			  }
		  }
	  }
	  return list;
  }
  
  private void enableDisableView(View view, boolean enabled) {
	  view.setEnabled(enabled);
	  
	  if ( view instanceof ViewGroup ) {
		  ViewGroup group = (ViewGroup)view;
		  for ( int idx = 0 ; idx < group.getChildCount() ; idx++ ) {
            enableDisableView(group.getChildAt(idx), enabled);
		  }
	  }
  }
  
 
  /** Called when the activity is first created. */
  @Override
  public void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);
    setContentView(R.layout.activity_main);

    spinner_device_list = (Spinner)findViewById(R.id.spinner_device_list);
    seekBar_angle = (SeekBar)findViewById(R.id.seekBar_angle);
    controlls = (RelativeLayout)findViewById(R.id.controlls);
    button_connect = (Button)findViewById(R.id.button_connect);
    textView_messages = (TextView)findViewById(R.id.textView_messages);
    textView_messages.setMovementMethod(new ScrollingMovementMethod());

    btAdapter = BluetoothAdapter.getDefaultAdapter();
    checkBTState();
    
    //получим список устройств.
    ArrayAdapter<String> adapter = new ArrayAdapter<String>(this, android.R.layout.simple_spinner_item, get_paired_device_list());
    spinner_device_list.setAdapter(adapter);
    enableDisableView(controlls, false);
    
    //Обработчик событий.
    handler = new Handler() {
    	public void handleMessage(android.os.Message msg) {
    		switch (msg.what) {
    			case MESSAGE_READ:
    				String str = new String((byte [])msg.obj);
    				textView_messages.append(str);
    			    
    				if ( textView_messages.getLayout() != null ) {
	    				int scrollAmount = textView_messages.getLayout().getLineTop(textView_messages.getLineCount()) - textView_messages.getHeight();
	    			    if (scrollAmount > 0)
	    			    	textView_messages.scrollTo(0, scrollAmount);
	    			    else
	    			    	textView_messages.scrollTo(0, 0);
    				}
    				break;
    		}
        };
    };

    //изменения в трек баре.
    seekBar_angle.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
    	public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser){
    		Log.d(TAG, "progress:" + progress);
    		send_set_angle((progress / (float)seekBar.getMax() * 2.f - 1.f) * (float)Math.PI); 
    	}
    	public void onStartTrackingTouch(SeekBar seekBar) {}
    	public void onStopTrackingTouch(SeekBar seekBar) {}
    });
  }
  
  boolean connect(String address) {
	  Log.d(TAG, "connect_to_device: " + address);

	  if (btAdapter == null)
		  return false;
  
    // Set up a pointer to the remote node using it's address.
    BluetoothDevice device = btAdapter.getRemoteDevice(address);
   
    try {
    	btSocket = device.createRfcommSocketToServiceRecord(MY_UUID);
    } catch (Exception e) {
    	Log.e(TAG, e.getMessage());
    	return false;
    }
    btAdapter.cancelDiscovery();
   
    Log.d(TAG, "...Соединяемся...");
    try {
    	btSocket.connect();
    	Log.d(TAG, "...Соединение установлено и готово к передачи данных...");
    } catch (Exception e) {
    	try {
        btSocket.close();
    	} catch (Exception e2) {}
    	
    	Log.e(TAG, e.getMessage());
    	btSocket = null;
    	return false;
    }
     
    // Create a data stream so we can talk to server.
    Log.d(TAG, "...Создание Socket...");
    try {
    	outStream = btSocket.getOutputStream();
    	in_stream = btSocket.getInputStream();
    } catch (Exception e) {
    	outStream = null;
    	in_stream = null;
    	try {
    		btSocket.close();
    	} catch (Exception e2) {}

    	Log.e(TAG, e.getMessage());
    	btSocket = null;
    	return false;
    }
    read_thread = new ReadThread(handler);
    read_thread.start();
    
    return true;
  }
  
  void close(){
      Log.d(TAG, "close");
	  if (outStream != null) {
		  try {
			  in_stream.close();
			  outStream.flush();
		  } catch (Exception e) {
			  Log.e(TAG, e.getMessage());
		  }
	  }

      if (btSocket != null ){
		  try {
			  btSocket.close();
	      } catch (Exception e){
	    	  Log.e(TAG, e.getMessage());
	      }
      }
      
      if (read_thread != null){
    	  read_thread.interrupt();
    	  try {
    		  read_thread.join();
    	  } catch (Exception e) {
    		  Log.e(TAG, e.getMessage());
    	  }

    	  in_stream = null;
		  outStream = null;
      }
  }
  
  public void on_button_connect_click(View v) {	
	  if (outStream == null){
		  Object obj = spinner_device_list.getSelectedItem();
		  
		  if (obj != null) {
			  if (connect(obj.toString().split("\n")[1])){
				  enableDisableView(controlls, true);
				  button_connect.setText(getString(R.string.disconnect));
			  }
		  }
	  } else {
		  close();
		  enableDisableView(controlls, false);
		  button_connect.setText(getString(R.string.connect));
	  }
	  
  }
  
  public void on_button_clear_click(View v){
	  textView_messages.setText("");
  }
   
  @Override
  public void onResume() {
    super.onResume();
  }
 
  @Override
  public void onPause() {
    super.onPause();
    close();
  }
   
  private void checkBTState() {
    // Check for Bluetooth support and then check to make sure it is turned on
    // Emulator doesn't support Bluetooth and will return null
    if(btAdapter==null) { 
      Log.w(TAG, "Bluetooth не поддерживается");
    } else {
      if (btAdapter.isEnabled()) {
        Log.d(TAG, "...Bluetooth включен...");
      } else {
        //Prompt user to turn on Bluetooth
        Intent enableBtIntent = new Intent(btAdapter.ACTION_REQUEST_ENABLE);
        startActivityForResult(enableBtIntent, REQUEST_ENABLE_BT);
      }
    }
  }
 
  private void send_set_angle(float angle) {
	  Log.d(TAG, "send_set_angle angle:" + angle);
	  if (outStream != null ) {
		try {
			ByteBuffer buffer = ByteBuffer.allocate(100);
			buffer.order(ByteOrder.LITTLE_ENDIAN);
			buffer.put((byte)6);
			buffer.putFloat(angle);
			outStream.write(buffer.position());
			outStream.write(buffer.array(), 0, buffer.position());
			outStream.flush();
		} catch (IOException e) {
			Log.e(TAG, e.getMessage());
		}
	  }
  }
}

