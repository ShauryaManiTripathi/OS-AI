package services

import (
	"fmt"

	"github.com/sergi/go-diff/diffmatchpatch"
)

type DiffService struct {
	sessionManager *SessionManager
	fileService    *FileService
}

type DiffRequest struct {
	OriginalPath string `json:"originalPath"`
	ModifiedPath string `json:"modifiedPath"`
	Original     string `json:"original,omitempty"`
	Modified     string `json:"modified,omitempty"`
}

type PatchRequest struct {
	FilePath string `json:"filePath"`
	Original string `json:"original"`
	Patches  string `json:"patches"`
}

type DiffResponse struct {
	Patches string `json:"patches"`
}

func NewDiffService(sm *SessionManager, fs *FileService) *DiffService {
	return &DiffService{
		sessionManager: sm,
		fileService:    fs,
	}
}

func (ds *DiffService) GenerateDiff(sessionID string, req *DiffRequest) (*DiffResponse, error) {
	var originalContent, modifiedContent string
	
	// Get content either from files or directly from request
	if req.OriginalPath != "" {
		content, err := ds.fileService.ReadFile(sessionID, req.OriginalPath)
		if err != nil {
			return nil, err
		}
		originalContent = string(content)
	} else {
		originalContent = req.Original
	}
	
	if req.ModifiedPath != "" {
		content, err := ds.fileService.ReadFile(sessionID, req.ModifiedPath)
		if err != nil {
			return nil, err
		}
		modifiedContent = string(content)
	} else {
		modifiedContent = req.Modified
	}
	
	dmp := diffmatchpatch.New()
	diffs := dmp.DiffMain(originalContent, modifiedContent, false)
	patches := dmp.PatchMake(originalContent, diffs)
	patchesText := dmp.PatchToText(patches)
	
	fmt.Printf("[TERMINAL] Session %s: Generated diff between %s and %s\n", 
		sessionID, req.OriginalPath, req.ModifiedPath)
	
	return &DiffResponse{
		Patches: patchesText,
	}, nil
}

func (ds *DiffService) ApplyPatch(sessionID string, req *PatchRequest) (string, error) {
	dmp := diffmatchpatch.New()
	patches, err := dmp.PatchFromText(req.Patches)
	if err != nil {
		return "", err
	}
	
	result, applied := dmp.PatchApply(patches, req.Original)
	
	// Check if all patches were applied
	allApplied := true
	for _, v := range applied {
		if !v {
			allApplied = false
			break
		}
	}
	
	if !allApplied {
		fmt.Printf("[TERMINAL] Session %s: Warning - Not all patches were applied to %s\n", 
			sessionID, req.FilePath)
	}
	
	// If a file path is provided, update the file
	if req.FilePath != "" {
		if err := ds.fileService.UpdateFile(sessionID, req.FilePath, []byte(result)); err != nil {
			return "", err
		}
		fmt.Printf("[TERMINAL] Session %s: Applied patches to file %s\n", sessionID, req.FilePath)
	} else {
		fmt.Printf("[TERMINAL] Session %s: Generated patched content\n", sessionID)
	}
	
	return result, nil
}
