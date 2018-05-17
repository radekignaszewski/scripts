import java.io.IOException;
import java.io.OutputStream;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.io.ByteArrayInputStream;

import java.net.InetSocketAddress;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;

import java.text.SimpleDateFormat;
import java.util.Calendar;

import org.json.JSONObject;

import java.util.*;  
import javax.mail.*;  
import javax.mail.internet.*;  
 

/*
 * a simple static http server
 * Simple Webhook to listen on end point /aggstart and /aggfinish
 * Will check for batch completion status and send email if there is a problem 
 * Radek
*/
public class Webhook {

  public static void main(String[] args) throws Exception {
    HttpServer server = HttpServer.create(new InetSocketAddress(3030), 0);
    server.createContext("/aggfinish", new MyHandler());
    server.createContext("/aggstart", new MyHandler());
    server.setExecutor(null); // creates a default executor
    System.out.println("starting");
    server.start();
  }
  
  public static void sendMail(String sMessage, String batchid){
	  
	  String to = "ignaszewski@1bank.dbs.com";//change accordingly  
	  String from = "admin@atscale.com";//change accordingly  
	  String host = "localhost";//or IP address  
	
	 //Get the session object  
	  Properties properties = System.getProperties();  
	  properties.setProperty("mail.smtp.host", host);  
	  properties.setProperty("mail.smtp.port", "2525");  
	  Session session = Session.getDefaultInstance(properties);  
	
	 //compose the message  
	  try{  
	     MimeMessage message = new MimeMessage(session);  
	     message.setFrom(new InternetAddress(from));  
	     message.addRecipient(Message.RecipientType.TO,new InternetAddress(to));  
	     message.setSubject("Error in batch submission: " + batchid);  
	     
	     message.setText(sMessage);  
	     //message.setText("Hello, this is example of sending email  ");  
	
	     // Send message  
	     Transport.send(message);  
	     System.out.println("message sent successfully....");  
	
	  }
	  	catch (MessagingException mex) {mex.printStackTrace();
	  }  
  }  

  static class MyHandler implements HttpHandler {
    public void handle(HttpExchange exchange) throws IOException {

      Calendar cal = Calendar.getInstance();
      SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss.SSS");
        		
      InputStream in = exchange.getRequestBody(); 
      ByteArrayOutputStream _out = new ByteArrayOutputStream(); 
      byte[] buf = new byte[2048]; 
      int read = 0; 
      while ((read = in.read(buf)) != -1) { 
          _out.write(buf, 0, read); 
      }
      exchange.sendResponseHeaders(200, 0); 
      
      String response = "finished";
      OutputStream out = exchange.getResponseBody(); 
      in = new ByteArrayInputStream(_out.toByteArray()); 
      while ((read = in.read(buf)) != -1) { 
          out.write(buf, 0, read); 
      }

      String sPload = new String(buf);
      out.write(response.getBytes());
      System.out.println("uri is " + exchange.getRequestURI());
      System.out.println("time: " + sdf.format(cal.getTime()));
      System.out.println("request body: " + sPload);

      String request = exchange.getRequestURI().toString();
      if (request.contains("aggfinish")){
   
    	  try {
    		  JSONObject jo = new JSONObject(sPload);
		      String event_type = jo.getString("event_type");
		      if (event_type.equalsIgnoreCase("aggregate_batch_result")){
		          String status = jo.getString("error");
		          String batchid = jo.getString("id");
		          if (!status.equalsIgnoreCase("null")) {
		        	  System.out.println("Batch failed: " + status + " id: " + batchid);
		        	  // Send email notification
		        	  //sendMail("Batch failed: " + sPload, batchid);
		          } else {
		        	  System.out.println("Batch finished with success. Batch id: " + batchid);
		          }
		      }
    	  }
    	  catch (Exception e){
    		  System.out.println("Problem with the payload data sent to the webhook: " + e.toString());
    	  }
    	  
      }

      out.flush(); 
      exchange.close();    
    }
  }
}