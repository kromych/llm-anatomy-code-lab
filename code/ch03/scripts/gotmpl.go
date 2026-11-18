// gotmpl.go -- render a Go template of the kind Ollama keeps for a model,
// with Go's own text/template package and a stand-in for Ollama's data
//   go run gotmpl.go TEMPLATE MESSAGES.json [think|nothink]
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"text/template"
)

type Message struct {
	Role, Content, Thinking string
	ToolCalls               []any
}

func main() {
	src, _ := os.ReadFile(os.Args[1])
	raw, _ := os.ReadFile(os.Args[2])
	var msgs []Message
	if err := json.Unmarshal(raw, &msgs); err != nil {
		panic(err)
	}
	var system []string
	for _, m := range msgs {
		if m.Role == "system" {
			system = append(system, m.Content)
		}
	}
	data := map[string]any{
		"Messages": msgs, "System": strings.Join(system, "\n\n"),
		"Tools": nil, "IsThinkSet": len(os.Args) > 3,
		"Think": len(os.Args) > 3 && os.Args[3] == "think",
	}
	t := template.Must(template.New("").Parse(string(src)))
	var out strings.Builder
	if err := t.Execute(&out, data); err != nil {
		panic(err)
	}
	fmt.Printf("%q\n", out.String())
}
