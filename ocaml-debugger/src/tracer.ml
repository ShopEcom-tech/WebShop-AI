(** 
   WebShop-AI Agent Debugger
   Real-time tracer for AI agent execution
   
   This module provides step-by-step tracing of agent workflows,
   allowing developers to debug and optimize agent behavior.
*)

(** Trace event types *)
type event_type =
  | AgentStart
  | AgentEnd
  | LLMCall
  | LLMResponse
  | ToolCall
  | ToolResponse
  | MemoryRead
  | MemoryWrite
  | RAGQuery
  | RAGResults
  | Error
  | Warning
  | Debug

(** Convert event type to string *)
let event_type_to_string = function
  | AgentStart -> "AGENT_START"
  | AgentEnd -> "AGENT_END"
  | LLMCall -> "LLM_CALL"
  | LLMResponse -> "LLM_RESPONSE"
  | ToolCall -> "TOOL_CALL"
  | ToolResponse -> "TOOL_RESPONSE"
  | MemoryRead -> "MEMORY_READ"
  | MemoryWrite -> "MEMORY_WRITE"
  | RAGQuery -> "RAG_QUERY"
  | RAGResults -> "RAG_RESULTS"
  | Error -> "ERROR"
  | Warning -> "WARNING"
  | Debug -> "DEBUG"

(** A single trace event *)
type trace_event = {
  id: string;
  timestamp: float;
  event_type: event_type;
  agent_name: string;
  action: string;
  input: string option;
  output: string option;
  duration_ms: int option;
  metadata: (string * string) list;
  parent_id: string option;
}

(** A complete trace session *)
type trace_session = {
  session_id: string;
  user_id: string option;
  agent_name: string;
  events: trace_event list ref;
  start_time: float;
  mutable end_time: float option;
  mutable status: string;
}

(** Generate a unique ID *)
let generate_id () =
  let random_part = Random.int 1000000 |> string_of_int in
  let time_part = Unix.gettimeofday () |> string_of_float in
  Printf.sprintf "evt_%s_%s" time_part random_part

(** Create a new trace event *)
let create_event 
    ~event_type 
    ~agent_name 
    ~action 
    ?input 
    ?output 
    ?duration_ms
    ?parent_id
    ?(metadata=[])
    () =
  {
    id = generate_id ();
    timestamp = Unix.gettimeofday ();
    event_type;
    agent_name;
    action;
    input;
    output;
    duration_ms;
    metadata;
    parent_id;
  }

(** Create a new trace session *)
let create_session ~session_id ?user_id ~agent_name () =
  {
    session_id;
    user_id;
    agent_name;
    events = ref [];
    start_time = Unix.gettimeofday ();
    end_time = None;
    status = "running";
  }

(** Add an event to a session *)
let add_event session event =
  session.events := event :: !(session.events)

(** End a trace session *)
let end_session session =
  session.end_time <- Some (Unix.gettimeofday ());
  session.status <- "completed"

(** Mark session as failed *)
let fail_session session error_msg =
  session.end_time <- Some (Unix.gettimeofday ());
  session.status <- "failed";
  let error_event = create_event
    ~event_type:Error
    ~agent_name:session.agent_name
    ~action:"session_failed"
    ~output:error_msg
    ()
  in
  add_event session error_event

(** Convert an event to JSON *)
let event_to_json event =
  let open Yojson.Basic in
  `Assoc [
    ("id", `String event.id);
    ("timestamp", `Float event.timestamp);
    ("event_type", `String (event_type_to_string event.event_type));
    ("agent_name", `String event.agent_name);
    ("action", `String event.action);
    ("input", match event.input with Some i -> `String i | None -> `Null);
    ("output", match event.output with Some o -> `String o | None -> `Null);
    ("duration_ms", match event.duration_ms with Some d -> `Int d | None -> `Null);
    ("metadata", `Assoc (List.map (fun (k, v) -> (k, `String v)) event.metadata));
    ("parent_id", match event.parent_id with Some p -> `String p | None -> `Null);
  ]

(** Convert a session to JSON *)
let session_to_json session =
  let open Yojson.Basic in
  let events_json = List.map event_to_json (List.rev !(session.events)) in
  let duration = match session.end_time with
    | Some end_t -> end_t -. session.start_time
    | None -> Unix.gettimeofday () -. session.start_time
  in
  `Assoc [
    ("session_id", `String session.session_id);
    ("user_id", match session.user_id with Some u -> `String u | None -> `Null);
    ("agent_name", `String session.agent_name);
    ("status", `String session.status);
    ("start_time", `Float session.start_time);
    ("end_time", match session.end_time with Some e -> `Float e | None -> `Null);
    ("duration_seconds", `Float duration);
    ("event_count", `Int (List.length !(session.events)));
    ("events", `List events_json);
  ]

(** Save session to file *)
let save_session_to_file session filename =
  let json = session_to_json session in
  let oc = open_out filename in
  Yojson.Basic.pretty_to_channel oc json;
  close_out oc

(** Print session summary to stdout *)
let print_session_summary session =
  let event_count = List.length !(session.events) in
  let duration = match session.end_time with
    | Some end_t -> end_t -. session.start_time
    | None -> Unix.gettimeofday () -. session.start_time
  in
  Printf.printf "\n";
  Printf.printf "╔══════════════════════════════════════════════════════════╗\n";
  Printf.printf "║           WEBSHOP-AI AGENT TRACE SUMMARY                  ║\n";
  Printf.printf "╠══════════════════════════════════════════════════════════╣\n";
  Printf.printf "║ Session ID: %-46s ║\n" session.session_id;
  Printf.printf "║ Agent:      %-46s ║\n" session.agent_name;
  Printf.printf "║ Status:     %-46s ║\n" session.status;
  Printf.printf "║ Events:     %-46d ║\n" event_count;
  Printf.printf "║ Duration:   %-43.3f s ║\n" duration;
  Printf.printf "╚══════════════════════════════════════════════════════════╝\n";
  Printf.printf "\n"

(** Print detailed event timeline *)
let print_event_timeline session =
  Printf.printf "\n📊 EVENT TIMELINE:\n";
  Printf.printf "─────────────────────────────────────────────────────────────\n";
  List.iter (fun event ->
    let time_offset = event.timestamp -. session.start_time in
    let type_str = event_type_to_string event.event_type in
    let duration_str = match event.duration_ms with
      | Some d -> Printf.sprintf " (%dms)" d
      | None -> ""
    in
    Printf.printf "[%8.3fs] [%-15s] %s: %s%s\n"
      time_offset
      type_str
      event.agent_name
      event.action
      duration_str;
    (match event.input with
     | Some input when String.length input > 0 ->
         let truncated = if String.length input > 50 
           then String.sub input 0 47 ^ "..." 
           else input in
         Printf.printf "            └─ Input: %s\n" truncated
     | _ -> ());
    (match event.output with
     | Some output when String.length output > 0 ->
         let truncated = if String.length output > 50 
           then String.sub output 0 47 ^ "..." 
           else output in
         Printf.printf "            └─ Output: %s\n" truncated
     | _ -> ())
  ) (List.rev !(session.events))

(** Analyze session for performance issues *)
let analyze_performance session =
  Printf.printf "\n⚡ PERFORMANCE ANALYSIS:\n";
  Printf.printf "─────────────────────────────────────────────────────────────\n";
  
  (* Find LLM calls and their durations *)
  let llm_calls = List.filter (fun e -> e.event_type = LLMCall) !(session.events) in
  let llm_durations = List.filter_map (fun e -> e.duration_ms) llm_calls in
  
  if List.length llm_durations > 0 then begin
    let total_llm_time = List.fold_left (+) 0 llm_durations in
    let avg_llm_time = total_llm_time / List.length llm_durations in
    Printf.printf "📡 LLM Calls: %d\n" (List.length llm_calls);
    Printf.printf "   Total time: %dms\n" total_llm_time;
    Printf.printf "   Average time: %dms\n" avg_llm_time;
    if avg_llm_time > 2000 then
      Printf.printf "   ⚠️  Warning: LLM response times are slow (>2s)\n"
  end;
  
  (* Find tool calls *)
  let tool_calls = List.filter (fun e -> e.event_type = ToolCall) !(session.events) in
  if List.length tool_calls > 0 then
    Printf.printf "🔧 Tool Calls: %d\n" (List.length tool_calls);
  
  (* Find errors *)
  let errors = List.filter (fun e -> e.event_type = Error) !(session.events) in
  if List.length errors > 0 then
    Printf.printf "❌ Errors: %d\n" (List.length errors);
  
  (* Find warnings *)
  let warnings = List.filter (fun e -> e.event_type = Warning) !(session.events) in
  if List.length warnings > 0 then
    Printf.printf "⚠️  Warnings: %d\n" (List.length warnings)
