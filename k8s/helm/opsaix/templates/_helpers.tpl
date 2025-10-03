{{/*
Expand the name of the chart.
*/}}
{{- define "opsaix.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "opsaix.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "opsaix.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "opsaix.labels" -}}
helm.sh/chart: {{ include "opsaix.chart" . }}
{{ include "opsaix.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: ai-incident-response
app.kubernetes.io/part-of: opsaix
{{- end }}

{{/*
Selector labels
*/}}
{{- define "opsaix.selectorLabels" -}}
app.kubernetes.io/name: {{ include "opsaix.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "opsaix.serviceAccountName" -}}
{{- if .Values.security.serviceAccount.create }}
{{- default (include "opsaix.fullname" .) .Values.security.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.security.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Return the proper OpsAiX image name
*/}}
{{- define "opsaix.image" -}}
{{- $registryName := .Values.opsaix.image.registry -}}
{{- $repositoryName := .Values.opsaix.image.repository -}}
{{- $tag := .Values.opsaix.image.tag | toString -}}
{{- if .Values.global.imageRegistry }}
    {{- printf "%s/%s:%s" .Values.global.imageRegistry $repositoryName $tag -}}
{{- else if $registryName }}
    {{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- else -}}
    {{- printf "%s:%s" $repositoryName $tag -}}
{{- end -}}
{{- end -}}

{{/*
Return the proper Docker Image Registry Secret Names
*/}}
{{- define "opsaix.imagePullSecrets" -}}
{{- include "common.images.pullSecrets" (dict "images" (list .Values.opsaix.image) "global" .Values.global) -}}
{{- end -}}